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
import datetime

#TODO: export to csv button for audit results
#TODO: for safety, we should reset pages/forms when something is updated or changed in the DB

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
        
        #Connect comboboxes to functions
        self.ui.auditTypeCombo.currentIndexChanged.connect(lambda: self.set_audit_menu())
        
        #Hide UI elements
        self.ui.batchStatusFrame.hide()
        self.ui.qsmackerUserFrame.hide()
        self.ui.defaultBranchFrame.hide()
        self.ui.auditResultsFrame.hide()
        self.ui.killJobBtn.hide()
        
        #populate rts_users to compare audits against
        self.rts_users = sql.Connection().get_rts_users()

    def create_popup(self, title, text, icon, buttons):
        self.popup = QMessageBox()
        self.popup.setWindowTitle(title)
        self.popup.setText(text)
        self.popup.setIcon(icon)
        self.popup.setStandardButtons(buttons)
        self.x = self.popup.exec_()

    def run_audit(self):
        sql_connection = sql.Connection()
        if self.ui.auditTypeCombo.currentText() == "RTU (by RefNo)":
            result = sql_connection.audit_rtu_by_refno(self.ui.auditSearchBox.text())
        if self.ui.auditTypeCombo.currentText() == "RTU (by SerialNo)":
            result = sql_connection.audit_rtu_by_serialno(self.ui.auditSearchBox.text())
            if result == "no refno":
                self.create_popup("No results found", "No results found for that SerialNo, please check the SerialNo and try again", QMessageBox.Warning, QMessageBox.Ok)
            else:
                keys_to_exclude = ["DateAction", "UserID", "SocketID", "DateAndTimeServiced", "ID", "IpPublic", "ColumnsUpdated"]
                #print(result)
                self.ui.auditResultsFrame.show()
                self.ui.auditResultsTable.setRowCount(0)
                self.ui.auditResultsTable.setColumnCount(5)
                self.ui.auditResultsTable.setHorizontalHeaderLabels(["DateAction", "User", "TextValue", "NewValue", "PreviousValue"])
                # Compare dictionaries and append necessary values to auditResultsTable
                for row in range(len(result) - 1):
                    current_dict = result[row]
                    next_dict = result[row + 1]
                    for key, value in current_dict.items():
                        if key in next_dict and value != next_dict[key]:
                            text_value = key
                            if text_value in keys_to_exclude:
                                continue
                            new_value = value
                            previous_value = next_dict[key]
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
                                d = datetime.datetime.strptime(str(date_action), '%Y-%m-%d %H:%M:%S.%f')
                                self.ui.auditResultsTable.insertRow(row_number)
                                self.ui.auditResultsTable.setItem(row_number, 2, QtWidgets.QTableWidgetItem(text_value))
                                self.ui.auditResultsTable.setItem(row_number, 3, QtWidgets.QTableWidgetItem(str(new_value)))
                                self.ui.auditResultsTable.setItem(row_number, 4, QtWidgets.QTableWidgetItem(str(previous_value)))
                                self.ui.auditResultsTable.setItem(row_number, 0, QtWidgets.QTableWidgetItem(str(d.strftime('%Y-%m-%d %H:%M:%S'))))
                                self.ui.auditResultsTable.setItem(row_number, 1, QtWidgets.QTableWidgetItem(user))


        if self.ui.auditTypeCombo.currentText() == "Branch":
            result = sql_connection.audit_branch(self.ui.auditSearchBox.text())
            if result == "no results":
                self.create_popup("No results found", "No results found for that Branch, please check the Branch and try again", QMessageBox.Warning, QMessageBox.Ok)
            else:
                keys_to_exclude = ["DateAction", "ID", "ColumnsUpdated", "UserID"]
                self.ui.auditResultsFrame.show()
                self.ui.auditResultsTable.setRowCount(0)
                self.ui.auditResultsTable.setColumnCount(5)
                self.ui.auditResultsTable.setHorizontalHeaderLabels(["DateAction", "User", "TextValue", "NewValue", "PreviousValue"])
                for row in range(len(result) - 1):
                    current_dict = result[row]
                    next_dict = result[row + 1]
                    for key, value in current_dict.items():
                        if key in next_dict and value != next_dict[key]:
                            text_value = key
                            if text_value in keys_to_exclude:
                                continue
                            #need to if text_value is customerID or RegionID, then get the name of the customer or region, but I has the dumb, brain is tired
                            if text_value == "CustomerID":
                                text_value = sql_connection.get_customer_name(value)
                            if text_value == "RegionID":
                                text_value = sql_connection.get_region_name(value)
                                #need to if text_value is customerID or RegionID, then get the name of the customer or region
                            new_value = value
                            previous_value = next_dict[key]
                            date_action = str(current_dict["DateAction"]).replace(microsecond=0) 
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
                                d = datetime.datetime.strptime(str(date_action), '%Y-%m-%d %H:%M:%S.%f')
                                self.ui.auditResultsTable.insertRow(row_number)
                                self.ui.auditResultsTable.setItem(row_number, 2, QtWidgets.QTableWidgetItem(text_value))
                                self.ui.auditResultsTable.setItem(row_number, 3, QtWidgets.QTableWidgetItem(str(new_value)))
                                self.ui.auditResultsTable.setItem(row_number, 4, QtWidgets.QTableWidgetItem(str(previous_value)))
                                self.ui.auditResultsTable.setItem(row_number, 0, QtWidgets.QTableWidgetItem(str(d.strftime('%Y-%m-%d %H:%M:%S'))))
                                self.ui.auditResultsTable.setItem(row_number, 1, QtWidgets.QTableWidgetItem(user))


        if self.ui.auditTypeCombo.currentText() == "Customer":
            result = sql_connection.audit_customer(self.ui.auditSearchBox.text())
            if result == "no results":
                self.create_popup("No results found", "No results found for that Customer, please check the Customer and try again", QMessageBox.Warning, QMessageBox.Ok)
            else:
                self.ui.auditResultsFrame.show()
                self.ui.auditResultsTable.setRowCount(1)
                self.ui.auditResultsTable.setColumnCount(4)
                self.ui.auditResultsTable.setHorizontalHeaderLabels(["DateAction", "User", "CustomerName", "BranchName"])
                for row in range(len(result)):
                    for column in range(2):
                        self.ui.auditResultsTable.setItem(row, column, QtWidgets.QTableWidgetItem(str(result[row][column])))

    def set_audit_menu(self):
        if self.ui.auditTypeCombo.currentText() == "RTU (by RefNo)":

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
        self.create_popup("Are you sure?", "Are you sure you want to insert a default machine for this branch?", QMessageBox.Question, QMessageBox.Ok | QMessageBox.Cancel)
        if self.x == QMessageBox.Ok:
            sql_connection = sql.Connection()
            branch_id = self.ui.branchIDLabel.text()
            branch_name = self.ui.branchNameLabel.text()
            sql_connection.insert_default_machine_sql(branch_id)
            self.ui.addDefaultMachineBtn.setEnabled(False)
            self.create_popup("Default Machine Added", "Default machine added successfully", QMessageBox.Information, QMessageBox.Ok)
            self.get_default_branch(branch_name)
            return True

    
    def get_default_branch(self, branch_name):
        sql_connection = sql.Connection()
        branch = sql_connection.find_branch_default_machine_status(branch_name)
        if branch == "no branch":
            self.create_popup("No branch found", "No branch found with that name, please check the name and try again", QMessageBox.Warning, QMessageBox.Ok)
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
        self.create_popup("Are you sure?", "Are you sure you want to update the permissions for this user?", QMessageBox.Question, QMessageBox.Yes | QMessageBox.Cancel)
        if self.x == QMessageBox.Yes:
            sql_connection = sql.Connection()
            result = sql_connection.update_permissions(user_id)
            if result:
                self.ui.permissionsLabel.setText("True")
                self.ui.setPermBtn.setEnabled(False)
                self.create_popup("Permissions Updated", "Permissions updated successfully", QMessageBox.Information, QMessageBox.Ok)
                email = alerting.EmailAlerts()
                email.recieverEmail.append(user_email)
                email.send_email("Qsmacker Permissions Updated", f"Qsmacker permissions updated for user with email {user_email} and user id {user_id}")
            if not result:
                self.create_popup("Permissions not updated", "Permissions not updated, some error. If it persists, please contact IT", QMessageBox.Critical, QMessageBox.Ok)
            return result
    
    def set_notification(self, notification, notificationBody):
        #create focus on notification, and make it hold focus until it is closed
        self.ui.notificaitonTitle.setText(notification)
        self.ui.notificationBody.setText(notificationBody)


    def get_user_compatibility(self, user_id):
        isValid = True
        sql_connection = sql.Connection()
        use_email = sql_connection.find_user(self.ui.qsmacker_email.text())
        print("the value of emails is: " + self.ui.qsmacker_email.text())
        if self.ui.qsmacker_email.text() == "":
            isValid = False
            self.create_popup("No email provided", "Please enter an email address", QMessageBox.Warning, QMessageBox.Ok)
        elif use_email == "not employee":
            isValid = False
            self.create_popup("Not an employee", "Please enter a valid Real Telematics email address", QMessageBox.Warning, QMessageBox.Ok)
        elif use_email == "no user":
            isValid = False
            self.create_popup("User not found", "No user found with that email address", QMessageBox.Warning, QMessageBox.Ok)
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
                self.create_popup("User has permissions already", "User has permissions already, please contact the IT department to update permissions", QMessageBox.Critical, QMessageBox.Ok)


    def get_qsmacker_job(self, job_name):
        sql_connection = sql.Connection()
        jobName = self.ui.qsmacker_jobname.text()
        job = sql_connection.find_job(jobName)
        print("the value of job is: ")
        print(job)
        if job == "no job":
            self.create_popup("No job found", "No job found with that name, please check the name and try again", QMessageBox.Warning, QMessageBox.Ok)
        elif job != "no job":
            self.ui.batchStatusFrame.show()
            counts = sql_connection.get_totals(job[0])
            self.ui.jobIDLabel.setText(str(job[0]))
            self.ui.qsmacker_jobname.setText(str(job[1]))
            self.ui.totalMachinesLabel.setText(str(counts[0]['Machines']))
            self.ui.totalCommandsLabel.setText(str(counts[1]['Commands']))
            if job[3] == 1:
                self.ui.jobStatusLabel.setText("Added")
            elif job[3] == 2:
                self.ui.jobStatusLabel.setText("Success")
            elif job[3] == 3:
                self.ui.jobStatusLabel.setText("Failed")
            self.ui.batch_list.clear()
            self.ui.batch_list.show()
            self.ui.batch_list.setRowCount(0)
            self.ui.batch_list.setColumnCount(5)
            self.ui.batch_list.setHorizontalHeaderLabels(["JobID", "SerialNo", "Description", "InsertDate", "BatchStatusId"])
            status_mapping = {
                1: "Added",
                2: "Loaded",
                3: "Success",
                4: "Failed",
                5: "No Device",
                6: "Manual User Failed",
                7: "Failed - lost comms"
            }
            for number in range(len(job[4])):
                batch_status_id = job[4][number]['BatchStatusId']
                jobStatusTranslated = status_mapping.get(batch_status_id, "Unknown")
                if jobStatusTranslated == "Added" or jobStatusTranslated == "Loaded":
                    self.ui.killJobBtn.setEnabled(True)
                    self.ui.killJobBtn.show()
                row_number = self.ui.batch_list.rowCount()
                self.ui.batch_list.insertRow(row_number)
                d = datetime.datetime.strptime(str(job[4][number]['insertDate']), '%Y-%m-%d %H:%M:%S.%f')
                self.ui.batch_list.setItem(row_number, 0, QtWidgets.QTableWidgetItem(str(job[4][number]['JobId'])))
                self.ui.batch_list.setItem(row_number, 1, QtWidgets.QTableWidgetItem(str(job[4][number]['serialNumber'])))
                self.ui.batch_list.setItem(row_number, 2, QtWidgets.QTableWidgetItem(str(job[4][number]['Description'])))
                self.ui.batch_list.setItem(row_number, 3, QtWidgets.QTableWidgetItem(str(d.strftime('%Y-%m-%d %H:%M:%S'))))
                self.ui.batch_list.setItem(row_number, 4, QtWidgets.QTableWidgetItem(jobStatusTranslated))


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('Fusion')
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
