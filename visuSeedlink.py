import matplotlib
import obspy.clients.seedlink.easyseedlink as sd
import pyqtgraph as pg
import sys
import re

from matplotlib.figure import Figure
from PySide6.QtCore import QRegularExpression, QRunnable, Slot, QThreadPool
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
                               QWidget)


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

    @Slot()  # QtCore.Slot
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''
        print('in thread')
        self.args[0].select_stream('XQ', 'CC247', '???')
        self.args[0].run()

    # def kill(self):
    #     self.args[0].close()

    # def get_stream(self, dataLineZ, dataLineN, dataLineE):
    #     self.client.select_stream('XQ', 'CC247', '???')
    #     self.client.run()


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
            self.started = False

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
            self.strLabel = QLabel('Stream')
            self.strField = QComboBox()
            self.strField.setFixedWidth(70)

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
            self.strLayout.addWidget(self.strField)
            self.strLayout.addStretch(0)
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
            self.graphWidgetZ = pg.PlotWidget(axisItems={'bottom': pg.DateAxisItem()})
            self.graphWidgetZ.setBackground('w')
            self.graphWidgetZ.showGrid(x=True, y=True)
            self.dataLineZ = self.graphWidgetZ.plot()


            self.graphWidgetN = pg.PlotWidget(axisItems={'bottom': pg.DateAxisItem()})
            self.graphWidgetN.setBackground('w')
            self.graphWidgetN.showGrid(x=True, y=True)
            self.dataLineN = self.graphWidgetN.plot()


            self.graphWidgetE = pg.PlotWidget(axisItems={'bottom': pg.DateAxisItem()})
            self.graphWidgetE.setBackground('w')
            self.graphWidgetE.showGrid(x=True, y=True)
            self.dataLineE = self.graphWidgetE.plot()

            self.streamBox = QGroupBox('Streams')
            self.streamLayout = QVBoxLayout()
            self.streamLayout.addWidget(self.graphWidgetZ)
            self.streamLayout.addWidget(self.graphWidgetN)
            self.streamLayout.addWidget(self.graphWidgetE)
            self.streamBox.setLayout(self.streamLayout)
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
            if 'HHZ' in trace.id:
                self.dataLineZ.setData(trace.data)
                self.graphWidgetZ.update()

            if 'HHN' in trace.id:
                self.dataLineN.setData(trace.data)
                self.graphWidgetN.update()

            if 'HHE' in trace.id:
                self.dataLineE.setData(trace.data)
                self.graphWidgetE.update()

            self.streamLayout.update()

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
            for i in streams:
                self.strField.addItem(i)

        def plot_trace(self):
            try:
                if self.worker:
                    self.client.close()
            except:
                self.threadpool = QThreadPool()
                self.worker = Worker(self.client)
                self.threadpool.start(self.worker)

    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    app.exec()


if __name__ == "__main__":
    main()
