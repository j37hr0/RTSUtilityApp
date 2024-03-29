import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QMessageBox, QInputDialog, QDialog
import sql
import alerting
import mainWindow_dark
from Custom_Widgets.Widgets import *
import os
import datetime
import csv


#TODO: look at concurrency issues with the DB, and how to handle them  https://realpython.com/python-pyqt-qthread/
#TODO: retest all the audit pages after refactoring the time parsing with a try/catch

# class Worker(QtCore.Qobject):
#     finished = QtCore.pyqtSignal()
#     progress = QtCore.pyqtSignal(int)
#     def run(self):
#         for i in range(100):
#             time.sleep(0.1)
#             self.progress.emit(i)
#         self.finished.emit()


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        QMainWindow.__init__(self)
        self.ui = mainWindow_dark.Ui_MainWindow()
        self.ui.setupUi(self)
        loadJsonStyle(self, self.ui)
        self.show()
        self.ui.mainPages.setCurrentIndex(0)
        
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
        self.ui.killJobBtn.clicked.connect(lambda: self.fail_qsmacker_job(self.ui.jobIDLabel.text()))
        self.ui.setPermBtn.clicked.connect(lambda: self.update_user_permissions())
        self.ui.branchSearchBtn.clicked.connect(lambda: self.get_default_branch(self.ui.branchSearch.text()))
        self.ui.auditSearchBtn.clicked.connect(lambda: self.select_audit())
        self.ui.addDefaultMachineBtn.clicked.connect(lambda: self.insert_default_machine())
        self.ui.downloadAuditBtn.clicked.connect(lambda: self.handle_save_audit("auditResultsTable"))
        self.ui.updateHistoricalBtn.clicked.connect(lambda: self.update_historical())

        #Connect enter keypresses to lineedits
        self.ui.qsmacker_jobname.returnPressed.connect(lambda: self.get_qsmacker_job(self.ui.qsmacker_jobname.text()))
        self.ui.branchSearch.returnPressed.connect(lambda: self.get_default_branch(self.ui.branchSearch.text()))
        self.ui.qsmacker_email.returnPressed.connect(lambda: self.get_user_compatibility(self.ui.qsmacker_email.text()))
        self.ui.auditSearchBox.returnPressed.connect(lambda: self.select_audit())
        
        #Connect comboboxes to functions
        self.ui.auditTypeCombo.currentIndexChanged.connect(lambda: self.set_audit_menu())
        
        #Hide UI elements
        self.ui.batchStatusFrame.hide()
        self.ui.qsmackerUserFrame.hide()
        self.ui.defaultBranchFrame.hide()
        self.ui.auditResultsFrame.hide()
        self.ui.killJobBtn.hide()
        self.ui.downloadAuditBtn.hide()


        #populate rts_users to compare audits against
        self.rts_users = sql.Connection().get_rts_users()

    def handle_save_audit(self, widgetName):
        widget = getattr(self.ui, widgetName)
        path, ok = QFileDialog.getSaveFileName(self, "Save File", os.getenv("HOME"), "CSV (*.csv)")
        if ok:
            columns = range(widget.columnCount())
            header = [widget.horizontalHeaderItem(column).text() for column in columns]
            with open(path, 'w') as csvfile:
                writer = csv.writer(csvfile,dialect='excel', delimiter=',')
                writer.writerow(header)
                for row in range(widget.rowCount()):
                    writer.writerow([widget.item(row, column).text() for column in columns])

    def refresh(self):
        self.ui.updateHistoricalBtn.show()
        self.ui.updateHistoricalLine.setText("")
        self.ui.mainPages.setCurrentIndex(0)
        self.rts_users = sql.Connection().get_rts_users()
        self.ui.centerMenuContainer.collapseMenu()
        self.ui.rightMenuContainer.collapseMenu()
        self.ui.popupNotificationContainer.collapseMenu()
        self.ui.qsmacker_jobname.setText("")
        self.ui.branchSearch.setText("")
        self.ui.qsmacker_email.setText("")
        self.ui.auditSearchBox.setText("")
        self.ui.auditResultsTable.setRowCount(0)
        self.ui.auditResultsFrame.hide()
        self.ui.qsmackerUserFrame.hide()
        self.ui.defaultBranchFrame.hide()
        self.ui.batchStatusFrame.hide()
        self.ui.killJobBtn.hide()
        self.ui.setPermBtn.setEnabled(False)
        self.ui.addDefaultMachineBtn.setEnabled(False)
        self.ui.permissionsLabel.setText("")
        self.ui.hasDefaultMachineLabel.setText("")
        self.ui.jobIDLabel.setText("")
        self.ui.qsmacker_jobname.setText("")
        self.ui.totalMachinesLabel.setText("")
        self.ui.totalCommandsLabel.setText("")
        self.ui.jobStatusLabel.setText("")
        self.ui.batch_list.clear()
        self.ui.batch_list.setRowCount(0)
        self.ui.batch_list.setColumnCount(0)
        self.ui.batch_list.hide()
        self.ui.userIDLabel.setText("")
        self.ui.branchIDLabel.setText("")
        self.ui.branchNameLabel.setText("")
        self.ui.customerNameLabel.setText("")
        self.ui.auditTypeCombo.setCurrentIndex(0)
        self.ui.auditSearchBox.setPlaceholderText("RefNo...")
        self.ui.auditTypeLabel.setText("Enter RefNo: ")
        self.ui.auditSearchBox.setValidator(None)

    def create_popup(self, title, text, icon, buttons):
        self.popup = QMessageBox()
        self.popup.setWindowTitle(title)
        self.popup.setText(text)
        self.popup.setIcon(icon)
        self.popup.setStandardButtons(buttons)
        self.popup.setStyleSheet("background-color: #343b47;" "color: rgb(255, 255, 255);")    
        self.x = self.popup.exec_()

    def select_audit(self):
        if self.ui.auditTypeCombo.currentText() == "RTU (by RefNo)":
            self.run_audit_dual()
        elif self.ui.auditTypeCombo.currentText() == "RTU (by SerialNo)":
            self.run_audit_dual()
        elif self.ui.auditTypeCombo.currentText() == "Branch":
            self.run_audit_branch()
        elif self.ui.auditTypeCombo.currentText() == "Customer":
            self.run_audit_customer()
        elif self.ui.auditTypeCombo.currentText() == "User":
            self.run_audit_user()

    def handle_result(self, results, keys_excluded, audit_type):
        replace_items = ["CustomerID", "BranchID", "RegionID", "AgentID"]
        for row in range(len(results) - 1):
                    current_dict = results[row]
                    next_dict = results[row + 1]
                    for key, value in current_dict.items():
                        if key in next_dict and value != next_dict[key]:
                            text_value = key
                            if text_value in keys_excluded:
                                continue
                            new_value = value
                            previous_value = next_dict[key]
                            date_action = str(current_dict["DateAction"])
                            if text_value == "UserAction" and new_value == 1:
                                text_value = f"{audit_type} Created"
                            for user in self.rts_users:
                                if user['id'] == current_dict["UserID"]:
                                    user = user['email']
                                    break
                            else:
                                user = "User Email Unknown, ID is: " + str(current_dict["UserID"])
                            if text_value == "":
                                continue
                            if text_value in replace_items:
                                if text_value == "CustomerID":
                                    oldID = previous_value
                                    newID = new_value
                                    previous_value = sql.Connection().get_customername_by_customerid(oldID)["CustomerName"]
                                    new_value = sql.Connection().get_customername_by_customerid(newID)["CustomerName"]
                                elif text_value == "BranchID":
                                    oldID = previous_value
                                    print(previous_value)
                                    newID = new_value
                                    new_value = sql.Connection().get_branchname_by_branchid(newID)["BranchName"]
                                    previous_value = sql.Connection().get_branchname_by_branchid(oldID)["BranchName"]
                                elif text_value == "RegionID":
                                    newID = new_value
                                    oldID = previous_value
                                    previous_value = sql.Connection().get_regionname_by_regionid(oldID)["Description"]
                                    new_value = sql.Connection().get_regionname_by_regionid(newID)["Description"]
                                elif text_value == "AgentID":
                                    newID = new_value
                                    oldID = previous_value
                                    previous_value = sql.Connection().get_agentname_by_agentid(oldID)["Description"]
                                    new_value = sql.Connection().get_agentname_by_agentid(newID)["Description"]
                                row_number = self.ui.auditResultsTable.rowCount()
                                self.ui.auditResultsTable.insertRow(row_number) 
                                try: 
                                    d = datetime.datetime.strptime(str(date_action), '%Y-%m-%d %H:%M:%S.%f')
                                except ValueError:
                                    d = datetime.datetime.strptime(str(date_action), '%Y-%m-%d %H:%M:%S')
                                self.populate_audit_table(row_number, [str(d.strftime('%Y-%m-%d %H:%M:%S')), user, text_value, str(new_value), str(previous_value)], "auditResultsTable")
                                self.ui.auditSearchBtn.show()
                                self.ui.downloadAuditBtn.show()
                            else:
                                row_number = self.ui.auditResultsTable.rowCount()
                                self.ui.auditResultsTable.insertRow(row_number)
                                try: 
                                    d = datetime.datetime.strptime(str(date_action), '%Y-%m-%d %H:%M:%S.%f')
                                except ValueError:
                                    d = datetime.datetime.strptime(str(date_action), '%Y-%m-%d %H:%M:%S')
                                self.populate_audit_table(row_number, [str(d.strftime('%Y-%m-%d %H:%M:%S.%f')), user, text_value, str(new_value), str(previous_value)], "auditResultsTable")
                                self.ui.auditSearchBtn.show()
                                self.ui.downloadAuditBtn.show()
        if self.ui.auditResultsTable.item(0, 0) == None:
            self.ui.auditResultsFrame.hide()
            self.ui.downloadAuditBtn.hide()
            self.ui.auditSearchBtn.show()
            self.create_popup("No results found", f"{audit_type} was found, but no important changes exist in the DB.", QMessageBox.Warning, QMessageBox.Ok)
            return
                    
    def setup_columns(self, columnWidths, columnCount, columnHeaders, widgetName):
        widget = getattr(self.ui, widgetName)
        for column in range(columnCount):
            widget.setRowCount(0)
            widget.setColumnCount(columnCount)
            widget.setColumnWidth(column, columnWidths[column])
        widget.setHorizontalHeaderLabels(columnHeaders)

    def populate_audit_table(self, rowNumber, result, widgetName):
        widget = getattr(self.ui, widgetName)
        for column in range(len(result)):
            widget.setItem(rowNumber, column, QtWidgets.QTableWidgetItem(str(result[column])))
        widget.show()

    def run_audit_dual(self):
        self.ui.auditSearchBtn.hide()
        app.processEvents()
        if self.ui.auditSearchBox.text() == "":
            self.create_popup("No input", "Please enter a value to search for", QMessageBox.Warning, QMessageBox.Ok)
            self.ui.auditSearchBtn.show()
            return
        sql_connection = sql.Connection()
        if self.ui.auditTypeCombo.currentText() == "RTU (by RefNo)":
            type = "refno"
        if self.ui.auditTypeCombo.currentText() == "RTU (by SerialNo)":
            type = "serialno"
        result = sql_connection.audit_rtu(identifier=self.ui.auditSearchBox.text(), type=type)
        if result == "no refno":
            self.create_popup(f"No results found", f"No results found for that {type}, please check the {type} and try again", QMessageBox.Warning, QMessageBox.Ok)
            self.ui.auditSearchBtn.show()
        else:
            keys_to_exclude = ["DateAction", "UserID", "SocketID", "DateAndTimeServiced", "ID", "IpPublic", "ColumnsUpdated"]
            # print(result)
            self.setup_columns([120, 150, 120, 140, 140], 5, ["DateAction", "User", "TextValue", "NewValue", "PreviousValue"], "auditResultsTable")
            self.ui.auditResultsFrame.show()
            self.handle_result(result, keys_to_exclude, audit_type="RTU")
            self.ui.auditSearchBtn.show()

    def run_audit_branch(self):
        self.ui.auditSearchBtn.hide()
        app.processEvents()
        if self.ui.auditSearchBox.text() == "":
            self.create_popup("No input", "Please enter a value to search for", QMessageBox.Warning, QMessageBox.Ok)
            return
        self.setup_columns([120, 160, 140, 140, 140], 5, ["DateAction", "User", "TextValue", "NewValue", "PreviousValue"], "auditResultsTable")
        sql_connection = sql.Connection()
        if self.ui.auditTypeCombo.currentText() == "Branch":
            result = sql_connection.audit_branch(self.ui.auditSearchBox.text())
            if len(result) == 1:
                for key, value in result[0].items():
                    if key == "UserAction" and value == 1:
                        print("branch created path taken")
                        text_value = "Branch Created"
                        new_value = value
                        previous_value = "NA"
                        date_action = str(result[0]["DateAction"])
                        for user in self.rts_users:
                            if user['id'] == result[0]["UserID"]:
                                user = user['email']
                                break
                        else:
                            user = "User Email Unknown, ID is: " + str(result["UserID"])
                        if text_value == "":
                            continue
                        else:
                            row_number = self.ui.auditResultsTable.rowCount() 
                            try: 
                                d = datetime.datetime.strptime(str(date_action), '%Y-%m-%d %H:%M:%S.%f')
                            except ValueError:
                                d = datetime.datetime.strptime(str(date_action), '%Y-%m-%d %H:%M:%S')
                            self.populate_audit_table(row_number, [str(d.strftime('%Y-%m-%d %H:%M:%S')), user, text_value, str(new_value), str(previous_value)], "auditResultsTable")
                            self.ui.auditSearchBtn.show()
            if result == "no branch":
                self.create_popup("No results found", "No results found for that Branch, please check the Branch and try again", QMessageBox.Warning, QMessageBox.Ok)
                self.ui.auditSearchBtn.show()
            else:
                keys_to_exclude = ["DateAction", "ID", "ColumnsUpdated", "UserID"]
                self.ui.auditResultsFrame.show()
                self.handle_result(result, keys_to_exclude, audit_type="Branch")
                self.ui.auditSearchBtn.show()

    def run_audit_customer(self):
        self.ui.auditSearchBtn.hide()
        app.processEvents()
        if self.ui.auditSearchBox.text() == "":
            self.create_popup("No input", "Please enter a value to search for", QMessageBox.Warning, QMessageBox.Ok)
            self.ui.auditSearchBtn.show()
            return
        self.setup_columns([120, 160, 140, 140, 140], 5, ["DateAction", "User", "TextValue", "NewValue", "PreviousValue"], "auditResultsTable")
        keys_to_exclude = ["DateAction", "ID", "ColumnsUpdated", "UserID"]
        sql_connection = sql.Connection()
        if self.ui.auditTypeCombo.currentText() == "Customer":
            result = sql_connection.audit_customer(self.ui.auditSearchBox.text())
            if len(result) == 1:
                for key, value in result[0].items():
                    if key == "UserAction" and value == 1:
                        print("customer created path taken")
                        text_value = "Customer Created"
                        new_value = value
                        previous_value = "NA"
                        date_action = str(result[0]["DateAction"])
                        for user in self.rts_users:
                            if user['id'] == result[0]["UserID"]:
                                user = user['email']
                                break
                        else:
                            user = "User Email Unknown, ID is: " + str(result["UserID"])
                        if text_value == "":
                            pass
                        else:
                                row_number = self.ui.auditResultsTable.rowCount()
                                self.ui.auditResultsTable.insertRow(row_number)
                                try: 
                                    d = datetime.datetime.strptime(str(date_action), '%Y-%m-%d %H:%M:%S.%f')
                                except ValueError:
                                    d = datetime.datetime.strptime(str(date_action), '%Y-%m-%d %H:%M:%S')
                                self.populate_audit_table(row_number, [str(d.strftime('%Y-%m-%d %H:%M:%S')), user, text_value, str(new_value), str(previous_value)])
                                self.ui.auditSearchBtn.show()
            if result == "no customer":
                self.create_popup("No results found", "No results found for that Customer, please check the Customer and try again", QMessageBox.Warning, QMessageBox.Ok)
                self.ui.auditSearchBtn.show()
            else:
                self.ui.auditResultsFrame.show()
                self.handle_result(result, keys_to_exclude, audit_type="Customer")
                self.ui.auditSearchBtn.show()

    def run_audit_user(self):
        self.ui.auditSearchBtn.hide()
        app.processEvents()
        if self.ui.auditSearchBox.text() == "":
            self.create_popup("No input", "Please enter a value to search for", QMessageBox.Warning, QMessageBox.Ok)
            return
        sql_connection = sql.Connection()
        if self.ui.auditTypeCombo.currentText() == "User":
            result = sql_connection.audit_user(self.ui.auditSearchBox.text())
            if result == "no user":
                self.create_popup("No results found", "No results found for that User, please check the User and try again", QMessageBox.Warning, QMessageBox.Ok)
                self.ui.auditSearchBtn.show()
            else:
                keys_to_exclude = ["DateAction", "ID", "ColumnsUpdated", "UserID"]
                self.setup_columns([120, 160, 140, 140, 140], 5, ["DateAction", "User", "TextValue", "NewValue", "PreviousValue"], "auditResultsTable")
                self.ui.auditResultsFrame.show()
                self.handle_result(result, keys_to_exclude, audit_type="User")
                self.ui.auditSearchBtn.show()

    def set_audit_menu(self):
        if self.ui.auditTypeCombo.currentText() == "RTU (by RefNo)":
            self.ui.auditSearchBox.setValidator(None)
            self.ui.auditTypeLabel.setText("Enter RefNo: ")
            self.ui.auditSearchBox.setPlaceholderText("RefNo...")
        if self.ui.auditTypeCombo.currentText() == "RTU (by SerialNo)":
            self.ui.auditSearchBox.setText("")
            self.ui.auditSearchBox.setValidator(QtGui.QRegExpValidator(QtCore.QRegExp("[0-9]{0,14}")))
            self.ui.auditTypeLabel.setText("Enter SerialNo: ")
            self.ui.auditSearchBox.setPlaceholderText("SerialNo...")
        if self.ui.auditTypeCombo.currentText() == "Branch":
            self.ui.auditTypeLabel.setText("Enter Branch Name: ")
            self.ui.auditSearchBox.setPlaceholderText("Branch Name...")
            self.ui.auditSearchBox.setValidator(None)
        if self.ui.auditTypeCombo.currentText() == "Customer":
            self.ui.auditTypeLabel.setText("Enter Customer Name: ")
            self.ui.auditSearchBox.setPlaceholderText("Customer Name...")
            self.ui.auditSearchBox.setValidator(None)
        if self.ui.auditTypeCombo.currentText() == "User":
            self.ui.auditTypeLabel.setText("Enter User Email: ")
            self.ui.auditSearchBox.setPlaceholderText("User Email...")
            self.ui.auditSearchBox.setValidator(None)

    def insert_default_machine(self):
        self.ui.addDefaultMachineBtn.hide()
        app.processEvents()
        self.create_popup("Are you sure?", "Are you sure you want to insert a default machine for this branch?", QMessageBox.Question, QMessageBox.Ok | QMessageBox.Cancel)
        if self.x == QMessageBox.Ok:
            sql_connection = sql.Connection()
            branch_id = self.ui.branchIDLabel.text()
            branch_name = self.ui.branchNameLabel.text()
            sql_connection.insert_default_machine_sql(branch_id)
            self.ui.addDefaultMachineBtn.setEnabled(False)
            self.create_popup("Default Machine Added", "Default machine added successfully", QMessageBox.Information, QMessageBox.Ok)
            self.get_default_branch(branch_name)
            self.refresh()
            self.ui.auditPageBtn.show()
            alerting = alerting.EmailAlerts()
            alerting.send_email("Default Machine Added", f"Default machine added for branch {branch_name}")
            return True
    
    def get_default_branch(self, branch_name):
        self.ui.branchSearchBtn.hide()
        app.processEvents()
        sql_connection = sql.Connection()
        branch = sql_connection.find_branch_default_machine_status(branch_name)
        if branch == "no branch":
            self.create_popup("No branch found", "No branch found with that name, please check the name and try again", QMessageBox.Warning, QMessageBox.Ok)
            self.ui.branchSearchBtn.show()
            del branch
        elif branch[1]['HasDefaultMachine'] == 1:
            self.ui.defaultBranchFrame.show()
            self.ui.addDefaultMachineBtn.hide()
            self.ui.hasDefaultMachineLabel.setText("True")
            self.ui.branchIDLabel.setText(str(branch[0]['BranchID']))
            self.ui.branchNameLabel.setText(str(branch[0]['BranchName']))
            self.ui.customerNameLabel.setText(str(branch[0]['CustomerName']))
            self.ui.branchSearchBtn.show()
            del branch
        elif branch[1]['HasDefaultMachine'] == 0:
            ##There is some bug here where if you have searched for a previous branch that has a default machine, 
            ##and then one that DOESN'T have a default machine, the add default machine button will not appear
            self.ui.addDefaultMachineBtn.show()
            self.ui.defaultBranchFrame.show()
            self.ui.hasDefaultMachineLabel.setText("False")
            self.ui.branchIDLabel.setText(str(branch[0]['BranchID']))
            self.ui.branchNameLabel.setText(str(branch[0]['BranchName']))
            self.ui.customerNameLabel.setText(str(branch[0]['CustomerName']))
            self.ui.branchSearchBtn.show()
            del branch

    def update_user_permissions(self):
        self.ui.setPermBtn.hide()
        app.processEvents()
        user_id = self.ui.userIDLabel.text()
        user_email = self.ui.qsmacker_email.text()
        self.create_popup("Are you sure?", "Are you sure you want to update the permissions for this user?", QMessageBox.Question, QMessageBox.Yes | QMessageBox.Cancel)
        if self.x == QMessageBox.Yes:
            sql_connection = sql.Connection()
            result = sql_connection.update_permissions(user_id)
            if result:
                self.ui.permissionsLabel.setText("True")
                self.ui.setPermBtn.hide()
                self.create_popup("Permissions Updated", "Permissions updated successfully", QMessageBox.Information, QMessageBox.Ok)
                email = alerting.EmailAlerts()
                email.recieverEmail.append(user_email)
                email.send_email("Qsmacker Permissions Updated", f"Qsmacker permissions updated for user with email {user_email} and user id {user_id}")
                self.refresh()
            if not result:
                self.create_popup("Permissions not updated", "Permissions not updated, some error. If it persists, please contact IT", QMessageBox.Critical, QMessageBox.Ok)
                self.refresh()
            return result

    def set_notification(self, notification, notificationBody):
        # Create focus on notification, and make it hold focus until it is closed
        self.ui.popupNotificationContainer.show()
        self.ui.popupNotificationContainer.raise_()
        self.ui.popupNotificationContainer.activateWindow()
        self.ui.notificaitonTitle.setText(notification)
        self.ui.notificationBody.setText(notificationBody)
        self.ui.notificationBtn.click()

    def get_user_compatibility(self, user_id):
        self.ui.userSearchBtn.hide()
        app.processEvents()
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
                self.ui.setPermBtn.show()
            else:
                self.ui.setPermBtn.show()
                self.ui.permissionsLabel.setText("True")
                self.create_popup("User has permissions already", "User has permissions already, please contact the IT department to update permissions", QMessageBox.Critical, QMessageBox.Ok)
                self.refresh()
        self.ui.userSearchBtn.show()

    def get_qsmacker_job(self, job_name):
        ##TODO: remove the trailing spaces from job names, this looks like a fuzzy lookup
        self.ui.findJobBtn.hide()
        app.processEvents()
        sql_connection = sql.Connection()
        jobName = self.ui.qsmacker_jobname.text()
        job = sql_connection.find_job(jobName)
        print("the value of job is: ")
        print(job)
        if job == "no job":
            self.create_popup("No job found", "No job found with that name, please check the name and try again", QMessageBox.Warning, QMessageBox.Ok)
            self.ui.findJobBtn.show()
        elif job != "no job":
            #date_action = str(job[4])
            self.ui.batchStatusFrame.show()
            counts = sql_connection.get_totals(job[0])
            self.ui.jobIDLabel.setText(str(job[0]))
            self.ui.qsmacker_jobname.setText(str(job[1]))
            self.ui.totalMachinesLabel.setText(str(counts[0]['Machines']))
            self.ui.totalCommandsLabel.setText(str(counts[1]['Commands']))
            self.ui.userLabelQsmackerJob.setText(str(job[2]))
            if job[3] == 1:
                self.ui.jobStatusLabel.setText("Added")
            elif job[3] == 2:
                self.ui.jobStatusLabel.setText("Success")
            elif job[3] == 3:
                self.ui.jobStatusLabel.setText("Failed")
            self.ui.batch_list.clear()
            self.ui.batch_list.show()
            self.ui.batch_list.setRowCount(0)
            self.setup_columns([50, 60, 100, 180, 120, 80], 6, ["JobID", "SerialNo", "RefNo", "Description", "InsertDate", "BatchStatusId"], "batch_list")
            status_mapping = {
                1: "Added",
                2: "Loaded",
                3: "Success",
                4: "Failed",
                5: "No Device",
                6: "Manual User Failed",
                7: "Failed - lost comms"
            }
            print("the batch status ID we're getting is " + str(job[5]))
            for number in range(0, len(job[5])):
                batch_status_id = job[5][number]['BatchStatusId']
                jobStatusTranslated = status_mapping.get(batch_status_id, "Unknown")
                #THE BELOW IS FOR DEVING PURPOSES ONLY
                self.ui.killJobBtn.setEnabled(True)
                self.ui.killJobBtn.show()
                # if jobStatusTranslated == "Added" or jobStatusTranslated == "Loaded":
                #     self.ui.killJobBtn.setEnabled(True)
                #     self.ui.killJobBtn.show()
                row_number = self.ui.batch_list.rowCount()
                self.ui.batch_list.insertRow(row_number)
                date_action = job[4]
                try: 
                    d = datetime.datetime.strptime(str(date_action), '%Y-%m-%d %H:%M:%S.%f')
                except ValueError:
                    d = datetime.datetime.strptime(str(date_action), '%Y-%m-%d %H:%M:%S')
                self.populate_audit_table(row_number, [str(job[5][number]['JobId']), str(job[5][number]['serialNumber']), str(job[5][number]['refNo']), str(job[5][number]['Description']), str(d.strftime('%Y-%m-%d %H:%M:%S')), jobStatusTranslated], "batch_list")
                self.ui.findJobBtn.show()

    def fail_qsmacker_job(self, job_id):
        self.ui.killJobBtn.hide()
        app.processEvents()
        user_email = self.ui.userLabelQsmackerJob.text()
        self.create_popup("Are you sure?", "Are you sure you want to kill this job?", QMessageBox.Question, QMessageBox.Yes | QMessageBox.Cancel)
        if self.x == QMessageBox.Yes:
            sql_connection = sql.Connection()
            job_name = self.ui.qsmacker_jobname.text()
            #RESTORE THE JOB HERE VVV
            #sql_connection.fail_qsmacker_job_sql(job_id, CommandFail=3, BatchFail=3, JobFail=2)
            #FAIL THE JOB HERE VVV
            #sql_connection.fail_qsmacker_job_sql(job_id)
            self.create_popup("Job Failed", "Job failed successfully", QMessageBox.Information, QMessageBox.Ok)
            self.refresh()
            self.ui.mainPages.setCurrentIndex(5)
            self.ui.qsmacker_jobname.setText(job_name)
            self.ui.auditPageBtn.click()
            self.ui.auditPageBtn.show()
            alert = alerting.EmailAlerts()
            alert.recieverEmail.append(user_email)
            alert.send_email("Qsmacker Job Manually Failed", f"Qsmacker job from {user_email} with job name {job_name} has been manually failed.")
            return True
        elif self.x == QMessageBox.Cancel:
            self.ui.killJobBtn.show()

    def update_historical(self):
        self.ui.updateHistoricalBtn.hide()
        refno = self.ui.updateHistoricalLine.text()
        app.processEvents()
        self.create_popup("Are you sure?", "Are you sure you want to update the historical data?", QMessageBox.Question, QMessageBox.Yes | QMessageBox.Cancel)
        if self.x == QMessageBox.Yes:
            sql_connection = sql.Connection()
            result = sql_connection.update_historical_by_refno(refno)
            value = result[0][0]
            print(value)
            if value != "SerialNumber not Found":
                self.create_popup(f"Historical Updated", f"Historical updated successfully, row count: {value}", QMessageBox.Information, QMessageBox.Ok)
                self.refresh()
                return True
            if value == "SerialNumber not Found":
                self.create_popup(f"Historical not updated", f"Historical not updated, error: {value}. If it persists, please contact IT", QMessageBox.Critical, QMessageBox.Ok)
                self.refresh()
                return False  

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('Fusion')
    window = MainWindow()
    #example of how to set notification
    #window.set_notification("New Job", "A new job has been posted")
    sys.exit(app.exec_())
    
