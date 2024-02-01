# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '.\qsmackerpermissions.ui'
#
# Created by: PyQt5 UI code generator 5.15.9
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(400, 300)
        self.qsmacker_ok_btn = QtWidgets.QDialogButtonBox(Dialog)
        self.qsmacker_ok_btn.setGeometry(QtCore.QRect(30, 240, 341, 32))
        self.qsmacker_ok_btn.setOrientation(QtCore.Qt.Horizontal)
        self.qsmacker_ok_btn.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.qsmacker_ok_btn.setObjectName("qsmacker_ok_btn")
        self.qsmacker_email = QtWidgets.QTextEdit(Dialog)
        self.qsmacker_email.setGeometry(QtCore.QRect(20, 50, 181, 31))
        self.qsmacker_email.setObjectName("qsmacker_email")
        self.label = QtWidgets.QLabel(Dialog)
        self.label.setGeometry(QtCore.QRect(20, 20, 71, 16))
        self.label.setObjectName("label")
        self.label_2 = QtWidgets.QLabel(Dialog)
        self.label_2.setGeometry(QtCore.QRect(230, 20, 131, 16))
        self.label_2.setObjectName("label_2")
        self.find_id_btn = QtWidgets.QPushButton(Dialog)
        self.find_id_btn.setGeometry(QtCore.QRect(120, 90, 81, 23))
        self.find_id_btn.setObjectName("find_id_btn")
        self.user_id_label = QtWidgets.QLabel(Dialog)
        self.user_id_label.setGeometry(QtCore.QRect(240, 50, 81, 31))
        self.user_id_label.setObjectName("user_id_label")

        self.retranslateUi(Dialog)
        self.qsmacker_ok_btn.accepted.connect(Dialog.accept) # type: ignore
        self.qsmacker_ok_btn.rejected.connect(Dialog.reject) # type: ignore
        QtCore.QMetaObject.connectSlotsByName(Dialog)
        Dialog.setTabOrder(self.qsmacker_email, self.find_id_btn)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.label.setText(_translate("Dialog", "User Email: "))
        self.label_2.setText(_translate("Dialog", "User ID (Required): "))
        self.find_id_btn.setText(_translate("Dialog", "Find ID"))
        self.user_id_label.setText(_translate("Dialog", "UserID"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Dialog = QtWidgets.QDialog()
    ui = Ui_Dialog()
    ui.setupUi(Dialog)
    Dialog.show()
    sys.exit(app.exec_())