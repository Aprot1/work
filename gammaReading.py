import numpy as np
import os
from pathlib import Path
from PySide6.QtWidgets import *
from PySide6.QtCore import QTimer, QRegularExpression, Qt
from PySide6.QtGui import QRegularExpressionValidator
import pyqtgraph as pg
import serial as sr
from statistics import mean, stdev
import sys
import random
import time


def get_ports():
    p = ['COM%s' % (i + 1) for i in range(15)]  # Create the COMX list
    avPorts = []
    for i in p:  # Check each port if a serial device is connected on each port
        try:  # avPorts represents the list of serial ports, to choose from
            s = sr.Serial(i)
            s.close()
            avPorts.append(i)
        except (OSError, sr.SerialException):
            pass
    return avPorts


class MainWindow(QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()

        ##### Variables #####
        self.s = True  # COM connection
        self.st = False  # started
        self.x = []  # Graph axe
        self.xp = []  # x production
        self.y = []  # Graph axe
        self.yp = []  # y production
        self.delta = 30
        self.wSize = 20
        self.coeffVal = np.nan
        self.numValidator = QRegularExpressionValidator(QRegularExpression(r'\d+'))
        self.coeffValidator = QRegularExpressionValidator(QRegularExpression(r'[+-]?\d(\.\d+)?[Ee][+-]?\d+'))
        #####

        ##### Connection Frame #####
        stLabel = QLabel('Status:')
        self.status = QLabel('Disconnected')
        self.status.setStyleSheet('color : red')
        self.portCombo = QComboBox()
        ports = get_ports()
        for i in ports:  # Get which COM ports are used
            self.portCombo.addItem(i)
        connectButton = QPushButton('Connect')
        connectButton.clicked.connect(self.try_connect)

        # Layout
        self.connectionBox = QGroupBox('Connection')
        connectionBoxLayout = QHBoxLayout()
        connectionBoxLayout.addWidget(stLabel)
        connectionBoxLayout.addWidget(self.status)
        connectionBoxLayout.addWidget(self.portCombo)
        connectionBoxLayout.addWidget(connectButton)
        connectionBoxLayout.addStretch(0)
        self.connectionBox.setLayout(connectionBoxLayout)
        self.connectionBox.setFixedSize(350, 60)
        #####

        ##### Radiation Graph #####
        self.graphWidget = pg.PlotWidget(axisItems={'bottom': pg.DateAxisItem()})
        self.graphWidget.setBackground('w')
        self.graphWidget.showGrid(x=True, y=True)
        styles = {'color': '#000000'}
        self.graphWidget.setLabel('left', 'Gamma (\u03BCSv/h)', **styles)
        self.graphWidget.setLabel('bottom', 'Time', **styles)
        gamPen = pg.mkPen(color='b', width=2)
        self.dataLine = self.graphWidget.plot(self.x, self.y, pen=gamPen)
        #####

        ##### Production Graph #####
        self.prodGraph = pg.PlotWidget(axisItems={'bottom': pg.DateAxisItem()})
        self.prodGraph.setBackground('w')
        self.prodGraph.showGrid(x=True, y=True)
        self.prodGraph.setLabel('left', 'Production (n/s)')
        self.prodGraph.setLabel('bottom', 'Time')
        self.prodLine = self.prodGraph.plot(self.xp, self.yp, pen=gamPen)
        #####

        ##### Tabs #####
        self.tabWidget = QTabWidget()
        self.tabWidget.addTab(self.graphWidget, 'Radiation')
        self.tabWidget.addTab(self.prodGraph, 'Production')
        #####

        ##### Parameters Frame #####
        disp = QLabel('Display Window (mn)')
        self.dispVal = QLineEdit(str(self.wSize))
        self.dispVal.setValidator(self.numValidator)
        self.dispVal.setFixedWidth(40)
        self.dispVal.returnPressed.connect(self.change_wsize)
        self.dispVal.setAlignment(Qt.AlignRight)
        coeff = QLabel('Production Coeff')
        self.coeffLine = QLineEdit(str(self.coeffVal))
        self.coeffLine.setValidator(self.coeffValidator)
        self.coeffLine.setFixedWidth(60)
        self.coeffLine.returnPressed.connect(self.change_coeff)
        self.coeffLine.setAlignment(Qt.AlignRight)
        self.start = QPushButton('Start/Stop')
        self.start.clicked.connect(self.start_stop)
        self.start.setFixedWidth(70)

        # Layout
        paramBox = QGroupBox('Parameters')
        paramLayout = QVBoxLayout()
        sizeLay = QHBoxLayout()
        sizeLay.addWidget(disp)
        sizeLay.addWidget(self.dispVal)
        coeffLay = QHBoxLayout()
        coeffLay.addWidget(coeff)
        coeffLay.addWidget(self.coeffLine)
        paramLayout.addLayout(sizeLay)
        paramLayout.addLayout(coeffLay)
        paramLayout.addWidget(self.start)
        paramBox.setLayout(paramLayout)
        paramBox.setFixedWidth(200)
        #####

        ##### Stat Frame #####
        deltaLabel = QLabel('\u0394t (s)')
        self.deltaVal = QLineEdit(str(self.delta))
        self.deltaVal.setValidator(self.numValidator)
        self.deltaVal.setFixedWidth(40)
        self.deltaVal.returnPressed.connect(self.change_delta)
        self.deltaVal.setAlignment(Qt.AlignRight)
        mn = QLabel('Mean:')
        self.meanVal = QLabel('0 \u03BCSv/h')
        sig = QLabel('\u03C3:')
        self.sigVal = QLabel('0 \u03BCSv/h')
        mini = QLabel('Min:')
        self.miniVal = QLabel('0 \u03BCSv/h')
        maxi = QLabel('Max:')
        self.maxiVal = QLabel('0 \u03BCSv/h')

        # Layout
        statBox = QGroupBox('Stats')
        statLayout = QGridLayout()
        dLay = QHBoxLayout()
        dLay.addWidget(deltaLabel)
        dLay.addWidget(self.deltaVal)
        dLay.addStretch(0)
        meLay = QHBoxLayout()
        meLay.addWidget(mn)
        meLay.addWidget(self.meanVal)
        sigLay = QHBoxLayout()
        sigLay.addWidget(sig)
        sigLay.addWidget(self.sigVal)
        miLay = QHBoxLayout()
        miLay.addWidget(mini)
        miLay.addWidget(self.miniVal)
        maLay = QHBoxLayout()
        maLay.addWidget(maxi)
        maLay.addWidget(self.maxiVal)
        statLayout.addLayout(dLay, 0, 0)
        statLayout.addLayout(meLay, 1, 0)
        statLayout.addLayout(sigLay, 1, 1)
        statLayout.addLayout(miLay, 2, 0)
        statLayout.addLayout(maLay, 2, 1)
        statBox.setLayout(statLayout)
        statBox.setFixedWidth(250)
        #####

        ##### Final Layout #####
        widget = QWidget()
        botLay = QHBoxLayout()
        botLay.addWidget(paramBox)
        botLay.addWidget(statBox)
        botLay.addStretch(0)
        finalLayout = QVBoxLayout()
        finalLayout.addWidget(self.connectionBox)
        finalLayout.addWidget(self.tabWidget)
        finalLayout.addLayout(botLay)

        widget.setLayout(finalLayout)
        self.setCentralWidget(widget)
        #####

        ##### Timer to update graph #####
        self.timer = QTimer()
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.update_graph)
        self.timer.start()
        #####

    def try_connect(self):  # Connect to target
        try:
            self.s = sr.Serial(str(self.portCombo.currentText()), 19200, parity=sr.PARITY_EVEN, stopbits=sr.STOPBITS_TWO,
                               bytesize=sr.SEVENBITS)
            self.status.setText('Connected')
            self.status.setStyleSheet('color : green')

        except sr.serialutil.SerialException:
            self.s = None

    def start_stop(self):  # Start / stop the graph update
        if not self.st and self.s is not None:
            self.st = True
        else:
            self.st = False

    def update_graph(self):  # Update the graph each seconds and save data to file
        if self.st and self.s is not None:
            try:
                self.s.write('\x0701RM138\x03'.encode())  # send message to sensor to ask for data
                gam = self.s.read_until(b'\x03').decode()  # receive data
                gam = float(gam.split(' ')[1])
            except:
                gam = np.nan

            # Get time for datation
            now = time.time()

            # Set x and y values

            if len(self.x) > self.wSize*60:
                self.x = self.x[-self.wSize*60:]
                self.y = self.y[-self.wSize*60:]
            self.x.append(now)
            # self.y.append(gam)
            self.y.append(random.randint(0, 50))

            # Update the graph
            self.dataLine.setData(self.x, self.y)

            # Stats computation
            if self.delta <= len(self.y):
                values = self.y[-self.delta:]
            else:
                values = self.y
            me = mean(values)
            self.meanVal.setText(str(round(me, 3)) + ' \u03BCSv/h')
            ma = round(max(values), 3)
            self.maxiVal.setText(str(ma) + ' \u03BCSv/h')
            mi = round(min(values), 3)
            self.miniVal.setText(str(mi) + ' \u03BCSv/h')
            std = round(stdev(values), 3)
            self.sigVal.setText(str(std) + ' \u03BCSv/h')

            # Production Graph update
            if len(self.xp) >= self.wSize*60:
                self.xp = self.xp[1:]
                self.yp = self.yp[1:]
            self.xp.append(now)
            if self.coeffVal is not np.nan:
                self.yp.append(round(me*self.coeffVal, 3))
            else:
                self.yp.append(me)

            self.prodLine.setData(self.xp, self.yp)

            ##### File Handling #####
 #           now = time.gmtime(now)
 #           tod = time.strftime('%Y%m%d', now)
 #           now = time.strftime('%Y%m%d;%H%M%S', now)
 #           path = str(Path.cwd()) + '/data/'
 #           file = path + 'gamma' + tod + '.csv'
 #           toWrite = ';'.join([now, str(gam)]) + '\n'
 #           if not os.path.isdir(path):
 #               os.mkdir(path)
 #           if not os.path.isfile(file):
 #               f = open(file, 'w')
 #               f.write('Date;Time;Gamma\n')
 #               f.close()
 #           f = open(file, 'a')
 #           f.write(toWrite)
 #           f.close()
            ######

    def change_delta(self):
        self.delta = int(self.deltaVal.text())

    def change_wsize(self):
        self.wSize = int(self.dispVal.text())

    def change_coeff(self):
        self.coeffVal = float(self.coeffLine.text())


app = QApplication(sys.argv)

window = MainWindow()
window.show()

app.exec()
