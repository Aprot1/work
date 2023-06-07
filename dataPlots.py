from PySide6.QtWidgets import *
from PySide6.QtGui import QTextCursor
import pyqtgraph as pg
import sys


class MainWindow(QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()

        ##### File Loading #####
        browserButton = QPushButton('Browse')
        browserButton.clicked.connect(self.browse)
        self.fileList = QTextEdit()
        self.fileList.setReadOnly(True)

        fLay = QHBoxLayout()
        fLay.addWidget(browserButton)
        fLay.addWidget(self.fileList)
        #####

        widget = QWidget()
        widget.setLayout(fLay)
        self.setCentralWidget(widget)


    def browse(self):
        self.files = QFileDialog.getOpenFileNames(self)
        for i in self.files[0]:
            self.fileList.append(i)

app = QApplication(sys.argv)

window = MainWindow()
window.show()

app.exec()
