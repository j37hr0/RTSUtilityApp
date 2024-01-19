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



#TODO: for safety, we should reset pages/forms when something is updated or changed in the DB
#TODO: for a quick win, I can refactor the popup code into a function that takes in the title, text, icon and buttons
#TODO: when the app opens for auditing purposes, run a query to populate a dictionary with user emails and user ids for use in the audit table


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        QMainWindow.__init__(self)
        self.ui = mainWindow_dark.Ui_MainWindow()
        self.ui.setupUi(self)
        loadJsonStyle(self, self.ui)
        self.show()
        #Connect buttons to functions
        self.ui.settingsBtn.clicked.connect(lambda: self.ui.centerMenuContainer.slideMenu())
        self.ui.helpBtn.clicked.connect(lambda: self.ui.centerMenuContainer.slideMenu())
        self.ui.loginBtn.clicked.connect(lambda: self.ui.centerMenuContainer.slideMenu())
        self.ui.closeBtnCenter.clicked.connect(lambda: self.ui.centerMenuContainer.collapseMenu())
        self.ui.elipsesBtn.clicked.connect(lambda: self.ui.rightMenuContainer.slideMenu())
        self.ui.profileBtn.clicked.connect(lambda: self.ui.rightMenuContainer.slideMenu())
        self.ui.closeRightBtn.clicked.connect(lambda: self.ui.rightMenuContainer.collapseMenu())
        self.ui.closeNotificationBtn.clicked.connect(lambda: self.ui.popupNotificationContainer.collapseMenu())
        self.ui.userSearchBtn.clicked.connect(lambda: self.get_user_compatibility(self.ui.qsmacker_email.text()))
        self.ui.findJobBtn.clicked.connect(lambda: self.get_qsmacker_job(self.ui.qsmacker_jobname.text()))
        self.ui.killJobBtn.clicked.connect(lambda: self.kill_qsmacker_job(self.ui.jobIDLabel.text()))
        self.ui.setPermBtn.clicked.connect(lambda: self.update_user_permissions())
        self.ui.branchSearchBtn.clicked.connect(lambda: self.get_default_branch(self.ui.branchSearch.text()))
        self.ui.auditSearchBtn.clicked.connect(lambda: self.run_audit())
        self.ui.addDefaultMachineBtn.clicked.connect(lambda: self.insert_default_machine())
        
        #Connect enter keypresses to lineedits
        self.ui.qsmacker_jobname.returnPressed.connect(lambda: self.get_qsmacker_job(self.ui.qsmacker_jobname.text()))
        self.ui.branchSearch.returnPressed.connect(lambda: self.get_default_branch(self.ui.branchSearch.text()))
        self.ui.qsmacker_email.returnPressed.connect(lambda: self.get_user_compatibility(self.ui.qsmacker_email.text()))
        self.ui.auditSearchBox.returnPressed.connect(lambda: self.run_audit())
        self.ui.auditTypeCombo.currentIndexChanged.connect(lambda: self.set_audit_menu())
        
        #Hide UI elements
        self.ui.batchStatusFrame.hide()
        self.ui.qsmackerUserFrame.hide()
        self.ui.defaultBranchFrame.hide()
        self.ui.auditResultsFrame.hide()
        
        #populate rts_users to compare audits against
        self.rts_users = sql.Connection().get_rts_users()


    def run_audit(self):
        sql_connection = sql.Connection()
        if self.ui.auditTypeCombo.currentText() == "RTU (by RefNo)":
            result = sql_connection.audit_rtu_by_refno(self.ui.auditSearchBox.text())
            if result == "no refno":
                popup = QMessageBox()
                popup.setWindowTitle("No results found")
                popup.setText("No results found for that RefNo, please check the RefNo and try again")
                popup.setIcon(QMessageBox.Warning)
                popup.setStandardButtons(QMessageBox.Ok)
                popup.exec_()
            else:
                keys_to_exclude = ["DateAction", "UserID", "SocketID", "DateAndTimeServiced", "ID"]
                print(result)
                self.ui.auditResultsFrame.show()
                self.ui.auditResultsTable.setRowCount(1)
                self.ui.auditResultsTable.setColumnCount(5)
                self.ui.auditResultsTable.setHorizontalHeaderLabels(["DateAction", "User", "TextValue", "CurrentValue", "PreviousValue"])
                # Compare dictionaries and append necessary values to auditResultsTable
                #Find a way to exclude things like DateAction from being written to the auditResultsTable
                for row in range(len(result) - 1):
                    current_dict = result[row]
                    next_dict = result[row + 1]
                    for key, value in current_dict.items():
                        if key in next_dict and value != next_dict[key]:
                            text_value = key
                            if text_value in keys_to_exclude:
                                continue
                                #We probably need to remove the key:value pair here, then repeat the current loop
                            current_value = next_dict[key]
                            previous_value = value
                            date_action = str(current_dict["DateAction"])
                            for user in self.rts_users:
                                if user['id'] == current_dict["UserID"]:
                                    user = user['email']
                                    break
                            else:
                                user = "User Email Unknown, ID is: " + str(current_dict["UserID"])
                            if text_value == "":
                                continue
                            else:
                                row_number = self.ui.auditResultsTable.rowCount() 
                                self.ui.auditResultsTable.insertRow(row_number)
                                self.ui.auditResultsTable.setItem(row_number, 2, QtWidgets.QTableWidgetItem(text_value))
                                self.ui.auditResultsTable.setItem(row_number, 3, QtWidgets.QTableWidgetItem(str(current_value)))
                                self.ui.auditResultsTable.setItem(row_number, 4, QtWidgets.QTableWidgetItem(str(previous_value)))
                                self.ui.auditResultsTable.setItem(row_number, 0, QtWidgets.QTableWidgetItem(date_action))
                                self.ui.auditResultsTable.setItem(row_number, 1, QtWidgets.QTableWidgetItem(user))


        if self.ui.auditTypeCombo.currentText() == "RTU (by SerialNo)":
            result = sql_connection.audit_rtu_by_serialno(self.ui.auditSearchBox.text())
            if result == "no results":
                popup = QMessageBox()
                popup.setWindowTitle("No results found")
                popup.setText("No results found for that SerialNo, please check the SerialNo and try again")
                popup.setIcon(QMessageBox.Warning)
                popup.setStandardButtons(QMessageBox.Ok)
                popup.exec_()
            else:
                self.ui.auditResultsFrame.show()
                self.ui.auditResultsTable.setRowCount(len(result))
                self.ui.auditResultsTable.setColumnCount(5)
                self.ui.auditResultsTable.setHorizontalHeaderLabels(["DateAction", "User", "TextValue", "CurrentValue", "PreviousValue"])
                for row in range(len(result)):
                    for column in range(2):
                        self.ui.auditResultsTable.setItem(row, column, QtWidgets.QTableWidgetItem(str(result[row][column])))
                # Compare dictionaries and append necessary values to auditResultsTable
                for row in range(len(result) - 1):
                    current_dict = result[row]
                    next_dict = result[row + 1]
                    for key, value in current_dict.items():
                        if key in next_dict and value != next_dict[key]:
                            text_value = key
                            current_value = next_dict[key]
                            previous_value = value
                            date_action = current_dict["DateAction"]
                            user = current_dict["UserID"]
                            self.ui.auditResultsTable.setItem(row, 2, QtWidgets.QTableWidgetItem(text_value))
                            self.ui.auditResultsTable.setItem(row, 3, QtWidgets.QTableWidgetItem(str(current_value)))
                            self.ui.auditResultsTable.setItem(row, 4, QtWidgets.QTableWidgetItem(str(previous_value)))
                            self.ui.auditResultsTable.setItem(row, 0, QtWidgets.QTableWidgetItem(date_action))
                            self.ui.auditResultsTable.setItem(row, 1, QtWidgets.QTableWidgetItem(user))

        if self.ui.auditTypeCombo.currentText() == "Branch":
            result = sql_connection.audit_branch(self.ui.auditSearchBox.text())
            if result == "no results":
                popup = QMessageBox()
                popup.setWindowTitle("No results found")
                popup.setText("No results found for that Branch, please check the Branch and try again")
                popup.setIcon(QMessageBox.Warning)
                popup.setStandardButtons(QMessageBox.Ok)
                popup.exec_()
            else:
                self.ui.auditResultsFrame.show()
                self.ui.auditResultsTable.setRowCount(len(result))
                self.ui.auditResultsTable.setColumnCount(3)
                self.ui.auditResultsTable.setHorizontalHeaderLabels(["RefNo", "SerialNo", "some other one"])
                for row in range(len(result)):
                    for column in range(2):
                        self.ui.auditResultsTable.setItem(row, column, QtWidgets.QTableWidgetItem(str(result[row][column])))
        if self.ui.auditTypeCombo.currentText() == "Customer":
            result = sql_connection.audit_customer(self.ui.auditSearchBox.text())
            if result == "no results":
                popup = QMessageBox()
                popup.setWindowTitle("No results found")
                popup.setText("No results found for that Customer, please check the Customer and try again")
                popup.setIcon(QMessageBox.Warning)
                popup.setStandardButtons(QMessageBox.Ok)
                popup.exec_()
            else:
                self.ui.auditResultsFrame.show()
                self.ui.auditResultsTable.setRowCount(len(result))
                self.ui.auditResultsTable.setColumnCount(3)
                self.ui.auditResultsTable.setHorizontalHeaderLabels(["RefNo", "SerialNo", "some other one"])
                for row in range(len(result)):
                    for column in range(2):
                        self.ui.auditResultsTable.setItem(row, column, QtWidgets.QTableWidgetItem(str(result[row][column])))

    def set_audit_menu(self):
        if self.ui.auditTypeCombo.currentText() == "RTU (by RefNo)":
            #self.ui.auditResultsFrame.show()
            self.ui.auditTypeLabel.setText("Enter RefNo: ")
            self.ui.auditSearchBox.setPlaceholderText("RefNo...")
        if self.ui.auditTypeCombo.currentText() == "RTU (by SerialNo)":
            self.ui.auditTypeLabel.setText("Enter SerialNo: ")
            self.ui.auditSearchBox.setPlaceholderText("SerialNo...")
        if self.ui.auditTypeCombo.currentText() == "Branch":
            self.ui.auditTypeLabel.setText("Enter Branch Name: ")
            self.ui.auditSearchBox.setPlaceholderText("Branch Name...")
        if self.ui.auditTypeCombo.currentText() == "Customer":
            self.ui.auditTypeLabel.setText("Enter Customer Name: ")
            self.ui.auditSearchBox.setPlaceholderText("Customer Name...")
    
    
    def insert_default_machine(self):
        popup = QMessageBox()
        popup.setWindowTitle("Are you sure?")
        popup.setText("Are you sure you want to insert a default machine for this branch?")
        popup.setIcon(QMessageBox.Question)
        popup.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        x = popup.exec_()
        if x == QMessageBox.Ok:
            sql_connection = sql.Connection()
            branch_id = self.ui.branchIDLabel.text()
            branch_name = self.ui.branchNameLabel.text()
            sql_connection.insert_default_machine_sql(branch_id)
            self.ui.addDefaultMachineBtn.setEnabled(False)
            popup = QMessageBox()
            popup.setWindowTitle("Default Machine Added")
            popup.setText("Default machine added successfully")
            popup.setIcon(QMessageBox.Information)
            popup.setStandardButtons(QMessageBox.Ok)
            x = popup.exec_()
            self.get_default_branch(branch_name)
            return True

    
    def get_default_branch(self, branch_name):
        sql_connection = sql.Connection()
        branch = sql_connection.find_branch_default_machine_status(branch_name)
        if branch == "no branch":
            popup = QMessageBox()
            popup.setWindowTitle("No branch found")
            popup.setText("No branch found with that name, please check the name and try again")
            popup.setIcon(QMessageBox.Warning)
            popup.setStandardButtons(QMessageBox.Ok)
            popup.exec_()
            del branch
        elif branch[1]['HasDefaultMachine'] == 1:
            self.ui.defaultBranchFrame.show()
            self.ui.addDefaultMachineBtn.hide()
            self.ui.hasDefaultMachineLabel.setText("True")
            self.ui.branchIDLabel.setText(str(branch[0]['BranchID']))
            self.ui.branchNameLabel.setText(str(branch[0]['BranchName']))
            self.ui.customerNameLabel.setText(str(branch[0]['CustomerName']))
            del branch
        elif branch[1]['HasDefaultMachine'] == 0:
            ##There is some bug here where if you have searched for a previous branch that has a default machine, 
            ##and then one that DOESN'T have a default machine, the add default machine button will not appear
            self.ui.addDefaultMachineBtn.setEnabled(True)
            self.ui.defaultBranchFrame.show()
            self.ui.hasDefaultMachineLabel.setText("False")
            self.ui.branchIDLabel.setText(str(branch[0]['BranchID']))
            self.ui.branchNameLabel.setText(str(branch[0]['BranchName']))
            self.ui.customerNameLabel.setText(str(branch[0]['CustomerName']))
            del branch

    
    def update_user_permissions(self):
        user_id = self.ui.userIDLabel.text()
        user_email = self.ui.qsmacker_email.text()
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
        use_email = sql_connection.find_user(self.ui.qsmacker_email.text())
        print("the value of emails is: " + self.ui.qsmacker_email.text())
        if self.ui.qsmacker_email.text() == "":
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
            self.ui.userIDLabel.setText(str(sql_connection.find_user(self.ui.qsmacker_email.text())))
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
        jobName = self.ui.qsmacker_jobname.text()
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
