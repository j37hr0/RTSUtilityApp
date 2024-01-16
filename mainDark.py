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




#TODO: hover over buttons not working

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        QMainWindow.__init__(self)
        self.ui = mainWindow_dark.Ui_MainWindow()
        self.ui.setupUi(self)
        loadJsonStyle(self, self.ui)
        self.show()
        #button connects for center menu
        self.ui.settingsBtn.clicked.connect(lambda: self.ui.centerMenuContainer.slideMenu())
        self.ui.helpBtn.clicked.connect(lambda: self.ui.centerMenuContainer.slideMenu())
        self.ui.signinBtn.clicked.connect(lambda: self.ui.centerMenuContainer.slideMenu())
        #close btn for center menu
        self.ui.closeBtnCenter.clicked.connect(lambda: self.ui.centerMenuContainer.collapseMenu())
        #button connects for right menu
        self.ui.elipsesBtn.clicked.connect(lambda: self.ui.rightMenuContainer.slideMenu())
        self.ui.profileBtn.clicked.connect(lambda: self.ui.rightMenuContainer.slideMenu())
        self.ui.closeRightBtn.clicked.connect(lambda: self.ui.rightMenuContainer.collapseMenu())
        #self.ui.notificationBtn.clicked.connect(lambda: self.ui.popupNotificationContainer.slideMenu())

        #The problem with the UI code above lies in the JSON data not being read for individual widgets
        #we can try fix this by separating the widgets into their own json style files


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
