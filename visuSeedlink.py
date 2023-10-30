import subprocess
import sys
from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import QRegularExpressionValidator
from PySide6.QtWidgets import (QApplication,
                               QGroupBox,
                               QHBoxLayout,
                               QLabel,
                               QLineEdit,
                               QMainWindow,
                               QPushButton,
                               QVBoxLayout,
                               QWidget)


# MAIN FUNCTION #
def main():
    # Subclass QMainWindow to customize your application's main window
    class MainWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            # Regulars expressions
            self.ipValid = QRegularExpressionValidator(QRegularExpression(r'(\d{1,3}\.){3}\d{1,3}'))
            self.netValid = QRegularExpressionValidator(QRegularExpression('[A-Z]{1,6}'))

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
            self.netField = QLineEdit()
            self.netField.setFixedWidth(70)
            self.netField.setValidator(self.netValid)
            self.staLabel = QLabel('Station')
            self.staField = QLineEdit()
            self.staField.setFixedWidth(70)
            self.strLabel = QLabel('Stream')
            self.strField = QLineEdit()
            self.strField.setFixedWidth(70)

            # LAYOUT
            self.parametersBox = QGroupBox('Parameters')
            self.ipLayout = QVBoxLayout()
            self.ipLayout.addWidget(self.ipLabel)
            self.ipLayout.addWidget(self.ipField)
            self.ipLayout.addWidget(self.connectButton)
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
            ####

            ##############
            # STREAM BOX #
            ##############
            ####

            ################
            # FINAL LAYOUT #
            ################
            layout = QHBoxLayout()
            layout.addWidget(self.parametersBox)

            widget = QWidget()
            widget.setLayout(layout)
            self.setCentralWidget(widget)

        #############
        # FUNCTIONS #
        #############

        def try_connect(self):
            cmd = 'dir'
            process = subprocess.run(cmd, capture_output=True, shell=True)
            print(process.stdout.decode())

    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    app.exec()


if __name__ == "__main__":
    main()
