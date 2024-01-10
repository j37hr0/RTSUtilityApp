import mainUI
import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QMessageBox, QInputDialog, QDialog
from qsmackerpermissions import Ui_Dialog
import sql
import alerting
from qsmackerJobsearch import Ui_Dialog as Ui_Dialog2
import mainWindow_dark
from Custom_Widgets.Widgets import *
#import Custom_Widgets.Widgets as Widgets
import os



#TODO: create a Qsmacker Job Stopper - do input validation on the job to be cancelled 
#T

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        QMainWindow.__init__(self)
        self.ui = mainWindow_dark.Ui_MainWindow()
        self.ui.setupUi(self)
        loadJsonStyle(self, self.ui)
        self.show()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())

# app = QtWidgets.QApplication(sys.argv)
# MainWindow = QtWidgets.QMainWindow()
# ui = mainWindow_dark.Ui_MainWindow()
# ui.setupUi(MainWindow)


# MainWindow.show()
# sys.exit(app.exec_())
