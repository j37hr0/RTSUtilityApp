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





#TODO: link keyboard press of enter to buttons for search and user search

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
        self.ui.loginBtn.clicked.connect(lambda: self.ui.centerMenuContainer.slideMenu())
        #close btn for center menu
        self.ui.closeBtnCenter.clicked.connect(lambda: self.ui.centerMenuContainer.collapseMenu())
        #button connects for right menu
        self.ui.elipsesBtn.clicked.connect(lambda: self.ui.rightMenuContainer.slideMenu())
        self.ui.profileBtn.clicked.connect(lambda: self.ui.rightMenuContainer.slideMenu())
        self.ui.closeRightBtn.clicked.connect(lambda: self.ui.rightMenuContainer.collapseMenu())
        self.ui.closeNotificationBtn.clicked.connect(lambda: self.ui.popupNotificationContainer.collapseMenu())
        self.ui.userSearchBtn.clicked.connect(lambda: self.get_user_compatibility(self.ui.qsmacker_email.toPlainText()))
        self.ui.findJobBtn.clicked.connect(lambda: self.get_qsmacker_job(self.ui.qsmacker_jobname.toPlainText()))
        self.ui.killJobBtn.clicked.connect(lambda: self.kill_qsmacker_job(self.ui.jobIDLabel.text()))
        self.ui.batchStatusFrame.hide()
        self.ui.qsmackerUserFrame.hide()
        self.ui.setPermBtn.clicked.connect(lambda: self.update_user_permissions())
        #The problem with the UI code above lies in the JSON data not being read for individual widgets
        #we can try fix this by separating the widgets into their own json style files
    def update_user_permissions(self):
        user_id = self.ui.userIDLabel.text()
        user_email = self.ui.qsmacker_email.toPlainText()
        popup = QMessageBox()
        popup.setWindowTitle("User is compatible")
        popup.setText("Are you sure you want to update the permissions for this user?")
        popup.setIcon(QMessageBox.Question)
        popup.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
        x = popup.exec_()
        if x == QMessageBox.Yes:
            sql_connection = sql.Connection()
            result = sql_connection.update_permissions(user_id)
            if result:
                self.ui.permissionsLabel.setText("True")
                self.ui.setPermBtn.setEnabled(False)
                popup0 = QMessageBox()
                popup0.setWindowTitle("Permissions Updated")
                popup0.setText("Permissions updated successfully")
                popup0.setIcon(QMessageBox.Information)
                popup0.setStandardButtons(QMessageBox.Ok)
                x = popup0.exec_()
                email = alerting.EmailAlerts()
                email.recieverEmail.append(user_email)
                email.send_email("Qsmacker Permissions Updated", f"Qsmacker permissions updated for user with email {user_email} and user id {user_id}")
            if not result:
                popup1 = QMessageBox()
                popup1.setWindowTitle("Permissions not updated")
                popup1.setText("Permissions not updated, some error. If it persists, please contact IT")
                popup1.setIcon(QMessageBox.Critical)
                popup1.setStandardButtons(QMessageBox.Ok)
                x = popup1.exec_()
            return result
    
    def set_notification(self, notification, notificationBody):
        self.ui.notificaitonTitle.setText(notification)
        self.ui.notificationBody.setText(notificationBody)


    def get_user_compatibility(self, user_id):
        isValid = True
        sql_connection = sql.Connection()
        use_email = sql_connection.find_user(self.ui.qsmacker_email.toPlainText())
        print("the value of emails is: " + self.ui.qsmacker_email.toPlainText())
        if self.ui.qsmacker_email.toPlainText() == "":
            isValid = False
            popup = QMessageBox()
            popup.setWindowTitle("No email provided")
            popup.setText("Please enter an email address")
            popup.setIcon(QMessageBox.Warning)
            popup.setStandardButtons(QMessageBox.Ok)
            popup.exec_()
        elif use_email == "not employee":
            isValid = False
            popup = QMessageBox()
            popup.setWindowTitle("Not an employee")
            popup.setText("Please enter a valid Real Telematics email address")
            popup.setIcon(QMessageBox.Warning)
            popup.setStandardButtons(QMessageBox.Ok)
            popup.exec_()
        elif use_email == "no user":
            isValid = False
            popup = QMessageBox()
            popup.setWindowTitle("User not found")
            popup.setText("No user found with that email address")
            popup.setIcon(QMessageBox.Warning)
            popup.setStandardButtons(QMessageBox.Ok)
            popup.exec_()
        elif isValid:
            sql_connection = sql.Connection()
            self.ui.userIDLabel.setText(str(sql_connection.find_user(self.ui.qsmacker_email.toPlainText())))
            user_id = self.ui.userIDLabel.text()
            permissions = sql_connection.find_permissions_by_user_id(user_id)
            if not permissions:
                self.ui.qsmackerUserFrame.show()
                self.ui.permissionsLabel.setText("False")
                self.ui.setPermBtn.setEnabled(True)
            else:
                self.ui.setPermBtn.setEnabled(False)
                self.ui.permissionsLabel.setText("True")
                popup = QMessageBox()
                popup.setWindowTitle("User has permissions already")
                popup.setText("User has permissions already, please contact the IT department to update permissions")
                popup.setIcon(QMessageBox.Critical)
                popup.setStandardButtons(QMessageBox.Ok)
                x = popup.exec_()



    def get_qsmacker_job(self, job_name):
        sql_connection = sql.Connection()
        jobName = self.ui.qsmacker_jobname.toPlainText()
        job = sql_connection.find_job(jobName)
        if job == "no job":
            popup = QMessageBox()
            popup.setWindowTitle("No job found")
            popup.setText("No job found with that name, please check the name and try again")
            popup.setIcon(QMessageBox.Warning)
            popup.setStandardButtons(QMessageBox.Ok)
            popup.exec_()
        elif job != "no job":
            self.ui.batchStatusFrame.show()
            counts = sql_connection.get_totals(job[0])
            self.ui.jobIDLabel.setText(str(job[0]))
            self.ui.qsmacker_jobname.setText(str(job[1]))
            self.ui.totalMachinesLabel.setText(str(counts[0]['Machines']))
            self.ui.totalCommandsLabel.setText(str(counts[1]['Commands']))
            self.ui.batch_list.clear()
            for number in range(len(job[3])):
                #self.ui.batch_list.addItem(str(job[3][number][0]))
                row = f"ID: {job[3][number]['JobId']} - SerialNo: {job[3][number]['serialNumber']} - Description: {job[3][number]['Description']} - InsertDate: {job[3][number]['insertDate']} - BatchStatusId: {job[3][number]['BatchStatusId']} -']))"
                self.ui.batch_list.addItem(row)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    #example of how to set notification
    #window.set_notification("New Job", "A new job has been posted")
    sys.exit(app.exec_())
    

# app = QtWidgets.QApplication(sys.argv)
# MainWindow = QtWidgets.QMainWindow()
# ui = mainWindow_dark.Ui_MainWindow()
# ui.setupUi(MainWindow)


# MainWindow.show()
# sys.exit(app.exec_())
