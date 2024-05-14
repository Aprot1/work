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
    if date.day() < 10:
        day = '0' + str(date.day())
    else:
        day = str(date.day())
    if date.month() < 10:
        month = '0' + str(date.month())
    else:
        month = str(date.month())
    ans = '-'.join([str(date.year()), month, day])
    return ans


def check_day(dayToCheck, nn, ns):
    ansNn = pd.DataFrame(columns=['Date', 'Time (UTC)', 'Session'])
    ansNs = pd.DataFrame(columns=['Date', 'Time (UTC)', 'Session'])
    with open(TEMPFILE, 'r') as f:
        for num, line in enumerate(f):
            if dayToCheck in line:
                # print(f'day to check = {dayToCheck}, line = {line},')
                try:
                    session = linecache.getline(TEMPFILE, num)
                    # print(session)
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
                                tempNn = pd.DataFrame([[dayToCheck, time, session]],
                                                      columns=['Date', 'Time (UTC)', 'Session'])
                                ansNn = pd.concat([ansNn, tempNn], ignore_index=True)
                            if ns and ('Ns' in station):
                                tempNs = pd.DataFrame([[dayToCheck, time, session]],
                                                      columns=['Date', 'Time (UTC)', 'Session'])
                                ansNs = pd.concat([ansNs, tempNs], ignore_index=True)
                        num += 1
                        line = linecache.getline(TEMPFILE, num)
                except:
                    pass
        return ansNn, ansNs


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
                print(r.text)

            nnSessionDf = pd.DataFrame(columns=['Date', 'Time (UTC)', 'Session'])
            nsSessionDf = pd.DataFrame(columns=['Date', 'Time (UTC)', 'Session'])

            while start != end.addDays(1):
                nn, ns = check_day(startString, self.nnButton.isChecked(), self.nsButton.isChecked())
                if not nn.empty:
                    nnSessionDf = pd.concat([nnSessionDf, nn])
                if not ns.empty:
                    nsSessionDf = pd.concat([nsSessionDf, ns])
                start = start.addDays(1)
                startString = make_date_string(start)

            outputText = str()
            if not nnSessionDf.empty:
                outputText += 'Sessions for Nn : \n\n'
                nnSessionDf = nnSessionDf.reset_index()
                for i in nnSessionDf.index:
                    date = nnSessionDf.iloc[i, nnSessionDf.columns.get_loc('Date')]
                    time = nnSessionDf.iloc[i, nnSessionDf.columns.get_loc('Time (UTC)')]
                    session = nnSessionDf.iloc[i, nnSessionDf.columns.get_loc('Session')]
                    outputText += ' '.join((date, time, session))
                    outputText += '\n'
                outputText += '\n'
            if not nsSessionDf.empty:
                outputText += 'Sessions for Ns : \n\n'
                nsSessionDf = nsSessionDf.reset_index()
                for i in nsSessionDf.index:
                    date = nsSessionDf.iloc[i, nsSessionDf.columns.get_loc('Date')]
                    time = nsSessionDf.iloc[i, nsSessionDf.columns.get_loc('Time (UTC)')]
                    session = nsSessionDf.iloc[i, nsSessionDf.columns.get_loc('Session')]
                    outputText += ' '.join((date, time, session))
                    outputText += '\n'
            if len(outputText) > 0:
                self.output.setText(outputText)
                self.sessionBox.setVisible(True)

    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    app.exec()


if __name__ == "__main__":
    main()
