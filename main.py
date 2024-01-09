import mainUI
import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QMessageBox, QInputDialog, QDialog
from qsmackerpermissions import Ui_Dialog
import sql
import alerting
from qsmackerJobsearch import Ui_Dialog as Ui_Dialog2

#TODO: create a Qsmacker Job Stopper - do input validation on the job to be cancelled 
#T

app = QtWidgets.QApplication(sys.argv)
MainWindow = QtWidgets.QMainWindow()
ui = mainUI.Ui_MainWindow()
ui.setupUi(MainWindow)


class QsmackerDlg(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)


class QsmackerSearchDlg(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_Dialog2()
        self.ui.setupUi(self)


dlg = QsmackerDlg()  # Create an instance of QsmackerDlg
searchDlg = QsmackerSearchDlg() #Create an instance of QsmackerSearchDlg

#sql_connection = sql.Connection()

def openqsmackerwindow():
    dlg.exec_()

def openqsmackersearchwindow():
    searchDlg.exec_()

def update_user_permissions(user_id):
    sql_connection = sql.Connection()
    result = sql_connection.update_permissions(user_id)
    return result
    

def get_user_compatibility(user_id):
    isValid = True
    sql_connection = sql.Connection()
    use_email = sql_connection.find_user(dlg.ui.qsmacker_email.toPlainText())
    print("the value of emails is: " + dlg.ui.qsmacker_email.toPlainText())
    if dlg.ui.qsmacker_email.toPlainText() == "":
        isValid = False
        popup = QMessageBox()
        popup.setWindowTitle("No email provided")
        popup.setText("No email provided, please enter an email")
        popup.setIcon(QMessageBox.Critical)
        popup.setStandardButtons(QMessageBox.Ok)
        x = popup.exec_()
    if use_email == "not employee":
        isValid = False
        popup = QMessageBox()
        popup.setWindowTitle("Invalid email provided")
        popup.setText("Invalid email provided, user must be a Real Telematics employee")
        popup.setIcon(QMessageBox.Critical)
        popup.setStandardButtons(QMessageBox.Ok)
        x = popup.exec_()
    if use_email == "no user":
        isValid = False
        popup = QMessageBox()
        popup.setWindowTitle("No user found")
        popup.setText("No user found with that email, please check the email and try again")
        popup.setIcon(QMessageBox.Critical)
        popup.setStandardButtons(QMessageBox.Ok)
        x = popup.exec_()
    elif isValid:
        user_email = dlg.ui.qsmacker_email.toPlainText()    
        sql_connection = sql.Connection()
        dlg.ui.user_id_label.setText(str(sql_connection.find_user(dlg.ui.qsmacker_email.toPlainText())))
        user_id = dlg.ui.user_id_label.text()
        permissions = sql_connection.find_permissions_by_user_id(user_id)
        if not permissions:
            popup = QMessageBox()
            popup.setWindowTitle("User is compatible")
            popup.setText("User is compatible, has no permissions. Update permissions now?")
            popup.setIcon(QMessageBox.Question)
            popup.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
            x = popup.exec_()
            if x == QMessageBox.Yes:
                result = update_user_permissions(user_id)
                if result:
                    popup0 = QMessageBox()
                    popup0.setWindowTitle("Permissions Updated")
                    popup0.setText("Permissions updated successfully")
                    popup0.setIcon(QMessageBox.Information)
                    popup0.setStandardButtons(QMessageBox.Ok)
                    x = popup0.exec_()
                    email = alerting.EmailAlerts()
                    email.recieverEmail.append("jethro.cotton3@gmail.com")
                    email.send_email("Qsmacker Permissions Updated", f"Qsmacker permissions updated for user with email {user_email} and user id {user_id}")
                if not result:
                    popup1 = QMessageBox()
                    popup1.setWindowTitle("Permissions not updated")
                    popup1.setText("Permissions not updated, some error. If it persists, please contact IT")
                    popup1.setIcon(QMessageBox.Critical)
                    popup1.setStandardButtons(QMessageBox.Ok)
                    x = popup1.exec_()
        else:
            popup = QMessageBox()
            popup.setWindowTitle("User has permissions already")
            popup.setText("User has permissions already, please contact the IT department to update permissions")
            popup.setIcon(QMessageBox.Critical)
            popup.setStandardButtons(QMessageBox.Ok)
            x = popup.exec_()


def get_qsmacker_job(job_name):
    sql_connection = sql.Connection()
    jobName = searchDlg.ui.qsmacker_jobname.toPlainText()
    job = sql_connection.find_job(jobName)
    if job == "no job":
        popup = QMessageBox()
        popup.setWindowTitle("No job found")
        popup.setText("No job found with that name, please check the name and try again")
        popup.setIcon(QMessageBox.Critical)
        popup.setStandardButtons(QMessageBox.Ok)
        x = popup.exec_()
    else:
        counts = sql_connection.get_totals(job[0])
        searchDlg.ui.job_id.setText(str(job[0]))
        searchDlg.ui.qsmacker_jobname.setText(str(job[1]))
        searchDlg.ui.batch_list.clear()
        for number in range(len(job[3])):
            row = f"ID: {job[3][number]['JobId']} - SerialNo: {job[3][number]['serialNumber']} - Description: {job[3][number]['Description']} - InsertDate: {job[3][number]['insertDate']} - BatchStatusId: {job[3][number]['BatchStatusId']} -']))"
            searchDlg.ui.batch_list.addItem(row)
        searchDlg.ui.mac_total.setText(str(counts[0]['Machines']))
        searchDlg.ui.com_total.setText(str(counts[1]['Commands'])) 


def kill_qsmacker_job():
    sql_connection = sql.Connection()
    job = sql_connection.find_job(searchDlg.ui.qsmacker_jobname.toPlainText())
    job_id = job[0]
    emailAddresses = job[2]
    job_id = searchDlg.ui.job_id.text()
    popup = QMessageBox()
    popup.setWindowTitle("Confirm Job Kill")
    popup.setText(f"Are you sure you want to kill job with id {job_id}?")
    popup.setIcon(QMessageBox.Warning)
    popup.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
    x = popup.exec_()
    if x == QMessageBox.Ok:
        result = sql_connection.kill_job(job_id)
        if result:
            popup = QMessageBox()
            popup.setWindowTitle("Job killed")
            popup.setText(f"Job with id {job_id} has been killed")
            popup.setIcon(QMessageBox.Information)
            popup.setStandardButtons(QMessageBox.Ok)
            x = popup.exec_()
            email = alerting.EmailAlerts()
            email.recieverEmail.append(emailAddresses)
            print(email.recieverEmail)


searchDlg.ui.find_job_btn.clicked.connect(get_qsmacker_job)
dlg.ui.find_id_btn.clicked.connect(get_user_compatibility)
ui.permissions_btn.clicked.connect(openqsmackerwindow)
ui.batch_status_btn.clicked.connect(openqsmackersearchwindow)
searchDlg.ui.kill_job_btn.clicked.connect(kill_qsmacker_job)

MainWindow.show()
sys.exit(app.exec_())
