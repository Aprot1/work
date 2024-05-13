import html2text
import linecache
import re

import pandas as pd
import requests
import sys

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (QApplication,
                               QCheckBox,
                               QDateTimeEdit,
                               QGroupBox,
                               QHBoxLayout,
                               QLabel,
                               QLineEdit,
                               QMainWindow,
                               QPushButton,
                               QTextEdit,
                               QVBoxLayout,
                               QWidget)

# Constants
SESSIONREGEX = re.compile(r'>([A-Z]+\d*[A-Z]?)<')
TIMEREGEX = re.compile(r'\d{2}:\d{2}')
STATIONREGEX = re.compile(r'>([A-Z][a-z])<')
TEMPFILE = 'sched.txt'


def make_date_string(date):
    if date.month() < 10:
        month = '0' + str(date.month())
    else:
        month = str(date.month())
    datestring = '-'.join([str(date.year()), month, str(date.day())])
    return datestring


def check_day(dayToCheck, nn, ns):
    activeSessionNn = []
    activeSessionNs = []
    with open(TEMPFILE, 'r') as f:
        for num, line in enumerate(f):
            if dayToCheck in line:
                try:
                    session = linecache.getline(TEMPFILE, num)
                    session = re.findall(SESSIONREGEX, session)[0]
                    time = linecache.getline(TEMPFILE, num + 1)
                    time = re.findall(TIMEREGEX, time)[0]
                    print(f'{session} @ {time}')
                    num += 6
                    line = linecache.getline(TEMPFILE, num)
                    while '/ul' not in line:
                        if 'station-id' in line and 'removed' not in line:
                            num += 1
                            line = linecache.getline(TEMPFILE, num)
                            station = re.findall(STATIONREGEX, line)
                            if nn and 'Nn' in station:
                                activeSessionNn.append(dayToCheck)
                                activeSessionNn.append(time)
                            if ns and 'Ns' in station:
                                activeSessionNs.append(dayToCheck)
                                activeSessionNs.append(time)
                        num += 1
                        line = linecache.getline(TEMPFILE, num)
                    return session, activeSessionNn, activeSessionNs
                except:
                    pass
        return None, None, None

def main():
    # Main Window creation
    class MainWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle('Session Schedule')

            #################
            # PARAMETERS BOX#
            #################
            self.startDateLabel = QLabel('Starting date')
            self.startDate = QDateTimeEdit(QDate.currentDate())
            self.startDate.setCalendarPopup(True)
            self.endDateLabel = QLabel('Ending date')
            self.endDate = QDateTimeEdit(QDate.currentDate())
            self.endDate.setCalendarPopup(True)
            self.nnButton = QCheckBox('Nn')
            self.nsButton = QCheckBox('Ns')
            self.stations = QLineEdit()
            self.searchButton = QPushButton('Search')
            self.searchButton.clicked.connect(self.search_sessions)

            # Layout
            self.parametersBox = QGroupBox('Parameters')
            self.stDateLayout = QVBoxLayout()
            self.stDateLayout.addWidget(self.startDateLabel)
            self.stDateLayout.addWidget(self.startDate)
            self.endDateLayout = QVBoxLayout()
            self.endDateLayout.addWidget(self.endDateLabel)
            self.endDateLayout.addWidget(self.endDate)
            self.stationsLayout = QVBoxLayout()
            self.stationsLayout.addWidget(self.nnButton)
            self.stationsLayout.addWidget(self.nsButton)
            self.dateLayout = QHBoxLayout()
            self.dateLayout.addLayout(self.stDateLayout)
            self.dateLayout.addLayout(self.endDateLayout)
            self.dateLayout.addLayout(self.stationsLayout)
            self.pBox = QVBoxLayout()
            self.pBox.addLayout(self.dateLayout)
            self.pBox.addWidget(self.searchButton)
            self.parametersBox.setLayout(self.pBox)


            ###############
            # SESSIONS BOX#
            ###############
            self.output = QTextEdit()
            self.output.setReadOnly(True)

            # Layout
            self.sessionBox = QGroupBox('Planning')
            self.sessionLayout = QVBoxLayout()
            self.sessionLayout.addWidget(self.output)
            self.sessionBox.setLayout(self.sessionLayout)
            self.sessionBox.setVisible(False)

            ###############
            # FINAL LAYOUT#
            ###############
            finalLayout = QVBoxLayout()
            finalLayout.addWidget(self.parametersBox)
            finalLayout.addWidget(self.sessionBox)


            widget = QWidget()
            widget.setLayout(finalLayout)
            self.setCentralWidget(widget)


        ############
        # FUNCTIONS#
        ############
        def search_sessions(self):
            start = self.startDate.date()
            startString = make_date_string(start)

            end = self.endDate.date()

            r = requests.get('https://ivscc.gsfc.nasa.gov/sessions/2024/')

            with open(TEMPFILE, 'w') as f:
                f.write(r.text)
                # print(r.text)
            nnSessionDf = pd.DataFrame(columns=['Date', 'Time (UTC)', 'Session'])
            nsSessionDf = pd.DataFrame(columns=['Date', 'Time (UTC)', 'Session'])

            while start != end.addDays(1):
                session, nn, ns = check_day(startString, self.nnButton.isChecked(), self.nsButton.isChecked())
                if session is not None:
                    if nn:
                        tempNn = pd.DataFrame({'Date': [nn[0]],
                                               'Time (UTC)': [nn[1]],
                                               'Session': session
                                               })
                        nnSessionDf = pd.concat([nnSessionDf, tempNn])
                    if ns:
                        tempNs = pd.DataFrame({'Date': [ns[0]],
                                               'Time (UTC)': [ns[1]],
                                               'Session': session
                                               })
                        nsSessionDf = pd.concat([nsSessionDf, tempNs])
                start = start.addDays(1)
                startString = make_date_string(start)
            print(nnSessionDf)
            print(nsSessionDf)
                #outputText = []
                #for i in nnSessionDf.iterrows():
                #    outputText += str(i)
                #self.output.setText(str(outputText))
                #self.sessionBox.setVisible(True)

    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    app.exec()


if __name__ == "__main__":
    main()
