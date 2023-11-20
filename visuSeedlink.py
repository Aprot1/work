import matplotlib
import obspy.clients.seedlink.easyseedlink as sd
import pyqtgraph as pg
import sys
import re

from matplotlib.figure import Figure
from PySide6.QtCore import QRegularExpression, QRunnable, Slot, QThreadPool, Qt
from PySide6.QtGui import QRegularExpressionValidator
from PySide6.QtWidgets import (QApplication,
                               QComboBox,
                               QGroupBox,
                               QHBoxLayout,
                               QLabel,
                               QLineEdit,
                               QMainWindow,
                               QPushButton,
                               QVBoxLayout,
                               QWidget,
                               QCheckBox)


class Worker(QRunnable):
    '''
    Worker thread

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    :param callback: The function callback to run on this worker thread. Supplied args and
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function

    '''

    def __init__(self, *args, **kwargs):
        super(Worker, self).__init__()
        # Store constructor arguments (re-used for processing)
        # self.fn = fn
        self.args = args
        self.kwargs = kwargs

    '''
    args[0] = seedlink client
    args[1] = network
    args[2] = station
    args[3] = streams
    '''
    @Slot()  # QtCore.Slot
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''
        print('in thread')
        self.args[0].select_stream(self.args[1], self.args[2], ' '.join(self.args[3]))
        self.args[0].run()

    def kill(self):
        self.exit()

# MAIN FUNCTION #
def main():
    # Subclass QMainWindow to customize your application's main window
    class MainWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            # Regulars expressions
            self.ax = matplotlib.figure.Figure()
            self.client = None
            self.ipValid = QRegularExpressionValidator(QRegularExpression(r'(\d{1,3}\.){3}\d{1,3}'))
            self.netValid = QRegularExpressionValidator(QRegularExpression('[A-Z]{1,6}'))
            self.netRe = re.compile('network=\"([A-Z]{2})\"')
            self.staRe = re.compile('station name=\"(\w+)\"')
            self.streamRe = re.compile('seedname=\"([A-Z]{3})\"')
            self.checkList = []
            self.graphs = []
            self.dataLines = []
            self.streaming = False

            self.setWindowTitle('SeedLink Stream')

            ##################
            # PARAMETERS BOX #
            ##################
            self.ipLabel = QLabel('IP address')
            self.ipField = QLineEdit()
            self.ipField.setFixedWidth(130)
            self.ipField.setValidator(self.ipValid)
            self.connectButton = QPushButton('Connect')
            self.connectButton.clicked.connect(self.try_connect)
            self.netLabel = QLabel('Network')
            self.netField = QComboBox()
            self.netField.setFixedWidth(70)
            self.netField.setValidator(self.netValid)
            self.getButton = QPushButton('Start/Stop Stream')
            self.getButton.clicked.connect(self.plot_trace)
            self.staLabel = QLabel('Station')
            self.staField = QComboBox()
            self.staField.setFixedWidth(70)
            self.strLabel = QLabel('Streams')
            self.strLabel.setAlignment(Qt.AlignTop)
            # self.strLabel.setVisible(True)
            # self.str1 = QCheckBox()
            # self.str1.setVisible(0)
            # self.str2 = QCheckBox()
            # self.str2.setVisible(0)
            # self.str3 = QCheckBox()
            # self.str3.setVisible(0)
            # self.strField = QComboBox()
            # self.strField.setFixedWidth(70)

            # LAYOUT
            self.parametersBox = QGroupBox('Parameters')
            self.ipLayout = QVBoxLayout()
            self.ipLayout.addWidget(self.ipLabel)
            self.ipLayout.addWidget(self.ipField)
            self.ipLayout.addWidget(self.connectButton)
            self.ipLayout.addWidget(self.getButton)
            self.ipLayout.addStretch(0)
            self.netLayout = QVBoxLayout()
            self.netLayout.addWidget(self.netLabel)
            self.netLayout.addWidget(self.netField)
            self.netLayout.addStretch(0)
            self.staLayout = QVBoxLayout()
            self.staLayout.addWidget(self.staLabel)
            self.staLayout.addWidget(self.staField)
            self.staLayout.addStretch(0)
            self.strLayout = QVBoxLayout()
            self.strLayout.addWidget(self.strLabel)
            # self.strLayout.addStretch(0)
            self.parametersLayout = QHBoxLayout()
            self.parametersLayout.addLayout(self.ipLayout)
            self.parametersLayout.addLayout(self.netLayout)
            self.parametersLayout.addLayout(self.staLayout)
            self.parametersLayout.addLayout(self.strLayout)
            self.parametersBox.setLayout(self.parametersLayout)
            self.parametersBox.setFixedSize(600, 150)
            ####

            ##############
            # STREAM BOX #
            ##############
            self.streamBox = QGroupBox('Streams')
            self.streamLayout = QVBoxLayout()
            self.streamBox.setLayout(self.streamLayout)


            # self.graphWidget2 = pg.PlotWidget(axisItems={'bottom': pg.DateAxisItem()})
            # self.graphWidget2.setBackground('w')
            # self.graphWidget2.showGrid(x=True, y=True)
            # self.dataLine2 = self.graphWidget2.plot()
            #
            #
            # self.graphWidget3 = pg.PlotWidget(axisItems={'bottom': pg.DateAxisItem()})
            # self.graphWidget3.setBackground('w')
            # self.graphWidget3.showGrid(x=True, y=True)
            # self.dataLine3 = self.graphWidget3.plot()

            # self.streamBox = QGroupBox('Streams')
            # self.streamLayout = QVBoxLayout()
            # self.streamLayout.addWidget(self.graphWidget1)
            # self.streamLayout.addWidget(self.graphWidget2)
            # self.streamLayout.addWidget(self.graphWidget3)
            # self.streamBox.setLayout(self.streamLayout)
            # self.streamBox.setVisible(0)
            #####

            ################
            # FINAL LAYOUT #
            ################
            layout = QVBoxLayout()
            layout.addWidget(self.parametersBox)
            layout.addWidget(self.streamBox)

            widget = QWidget()
            widget.setLayout(layout)
            self.setCentralWidget(widget)

        #############
        # FUNCTIONS #
        #############
        def handle_data(self, trace):
            for i, j in enumerate(self.toStream):
                if j in trace.id:
                    self.dataLines[i].setData(trace.data)
                    self.graphs[i].update()
            # self.streamLayout.update()

        def try_connect(self):
            self.client = sd.create_client('100.96.1.2', on_data=self.handle_data)
            info = self.client.get_info('STREAMS')
            print(info)
            network = self.netRe.findall(info)[0]
            stations = self.staRe.findall(info)
            streams = self.streamRe.findall(info)
            self.netField.addItem(network)
            for i in stations:
                self.staField.addItem(i)
            for i in range(len(streams)):
                self.checkList.append(QCheckBox(streams[i]))
                self.strLayout.addWidget(self.checkList[i])

        def plot_trace(self):
            if self.streaming:
                # self.threadpool.thread()
                # self.client.close()
                self.streaming = False
            else:
                self.toStream = []
                n = 0
                for i in self.checkList:
                    if i.isChecked():
                        self.toStream.append(i.text())
                        self.graphs.append(pg.PlotWidget(axisItems={'bottom': pg.DateAxisItem()}))
                        self.graphs[n].setBackground('w')
                        self.graphs[n].showGrid(x=True, y=True)
                        self.dataLines.append(self.graphs[n].plot())
                        self.streamLayout.addWidget(self.graphs[n])
                        n += 1
                print(self.toStream)
                self.threadpool = QThreadPool()
                self.worker = Worker(self.client, self.netField.currentText(), self.staField.currentText(), self.toStream)
                self.threadpool.start(self.worker)
                self.streaming = True

    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    app.exec()


if __name__ == "__main__":
    main()
