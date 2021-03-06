#!/usr/bin/env python
# coding:utf-8
"""
Author : Vitaliy Zubriichuk
Contact : v@zubr.kiev.ua
Time    : 03.09.2021 11:56
"""

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QTimer, Qt
from PyQt5.Qt import QHBoxLayout

from gui.app_userCubePermissions import Ui_MainWindow

# from pyodbc import Error as SQLError
from db_connect import DBConnect
# from db_connect import DBConnect as sql
from log_error import writelog
from singleinstance import Singleinstance
import sys
import os
import getpass

server = 's-kv-center-s64'
db = 'PlanRC'
sql = DBConnect(server, db)
LastStateRole = QtCore.Qt.UserRole

class PopupInfoWindows(QWidget):
    def __init__(self):
        super().__init__()

    def checked_error(self):
        QMessageBox.critical(self, 'Ошибка',
                             'Роль не была выбрана',
                             QMessageBox.Ok, QMessageBox.Ok)

    def popup_remove_error(self):
        QMessageBox.critical(self, 'Ошибка',
                             'Ошибка при удалении роли',
                             QMessageBox.Ok, QMessageBox.Ok)

    def popup_add_error(self):
        QMessageBox.critical(self, 'Ошибка',
                             'Ошибка при добавлении роли',
                             QMessageBox.Ok, QMessageBox.Ok)

    def popup_remove_role_succesfull(self):
        QMessageBox.information(self, 'Удаление ролей',
                                'Выбранные роли были успешно удалены.',
                                QMessageBox.Ok, QMessageBox.Ok)

    def popup_add_role_succesfull(self):
        QMessageBox.information(self, 'Добавление ролей',
                                'Выбранные роли были успешно добавлены.',
                                QMessageBox.Ok, QMessageBox.Ok)

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Выход',
                                     'Вы уверены что хотите выйти?',
                                     QMessageBox.Yes | QMessageBox.No,
                                     QMessageBox.No)
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()


class CheckBoxStyle(QtWidgets.QProxyStyle):
    def subElementRect(self, element, option, widget=None):
        r = super().subElementRect(element, option, widget)
        if element == QtWidgets.QStyle.SE_ItemViewItemCheckIndicator:
            r.moveCenter(option.rect.center())
        return r


class CubeRolesApp(QtWidgets.QMainWindow, Ui_MainWindow, PopupInfoWindows):
    def __init__(self):
        super().__init__()
        self.setupUi(self)  # Это нужно для инициализации нашего дизайна
        self.setWindowIcon(QtGui.QIcon('resources/shopping.png'))
        self.userLogin = str
        self.listCubes = dict
        self.listActiveCubes = dict

        with sql:
            try:
                self.users = dict(sql.get_users())
            except Exception as e:
                writelog(e)

        # Add autocomplete for total list users
        completer = QCompleter(self.users.values())
        completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.input_search_user.setCompleter(completer)
        self.input_search_user.textChanged.connect(self.on_text_changed)

        self.button_get_user_info.setEnabled(False)
        self.button_get_user_info.clicked.connect(self.get_user_info)
        self.btn_add.clicked.connect(lambda:self.check_rows(1))
        self.btn_remove.clicked.connect(lambda:self.check_rows(0))

    def on_text_changed(self):
        self.button_get_user_info.setEnabled(bool(self.input_search_user.text()))

    """
        Функция принимает виджет таблицы и 
        стилизирует чекбоксы по центру
    """
    def checkbox_styling(self):
        widgets = [self.tableListCubes, self.tableActiveListCubes]
        for widget in widgets:
            checkbox_style = CheckBoxStyle(widget.style())
            widget.setStyle(checkbox_style)

    def get_user_info(self):
        self.checkbox_styling()
        UserFullName = self.input_search_user.text()
        with sql:
            userInfo = sql.get_user_info(UserFullName)
            self.info_userLogin.setText(userInfo[0])
            self.info_userShortName.setText(userInfo[1])
            self.info_userPosition.setText(userInfo[4])
            self.info_userBusiness.setText(userInfo[5])
            self.info_userDepartment.setText(userInfo[3])
            self.userLogin = userInfo[0]

            # build available cubes for user
            self.listCubes = dict(sql.get_list_cubes(self.userLogin))
            self.insert_into(self.tableListCubes, self.listCubes, 60, 50, 380)
            # build only active cubes for user
            self.listActiveCubes = dict(sql.get_list_active_cubes(self.userLogin))
            self.insert_into(self.tableActiveListCubes, self.listActiveCubes, 60, 50, 350)

    # функция работы с чекбоксами в списке
    def check_rows(self, type):
        ID = []
        listID = str
        if type == 1:
            countRows = len(self.listCubes)
            for i in range(countRows):
                checkboxItem = self.tableListCubes.item(i, 0)
                currentState = checkboxItem.checkState()
                if currentState == QtCore.Qt.Checked:
                    ID.append(self.tableListCubes.item(i, 1).text())
            listID = ', '.join(ID)
        elif type == 0:
            countRows = len(self.listActiveCubes)
            for i in range(countRows):
                checkboxItem = self.tableActiveListCubes.item(i, 0)
                currentState = checkboxItem.checkState()
                if currentState == QtCore.Qt.Checked:
                    ID.append(self.tableActiveListCubes.item(i, 1).text())
            listID = ', '.join(ID)
        if listID is not None and len(listID) != 0:
            with sql:
                status = sql.add_roles_to_user(self.userLogin, listID, type)
                if status[0] == 1:
                    if type == 1:
                        self.popup_add_role_succesfull()
                    elif type == 0:
                        self.popup_remove_role_succesfull()
                elif status == 0:
                    if type == 1:
                        self.popup_add_error()
                    elif type == 0:
                        self.popup_remove_error()
            self.get_user_info()


    @staticmethod
    def insert_into(widget, lists, wCol1, wCol2, wCol3):
        try:
            # create basic table window
            countRows = len(lists)
            widget.setRowCount(countRows)
            for row in range(countRows):
                item = QtWidgets.QTableWidgetItem()
                item.setTextAlignment(QtCore.Qt.AlignCenter)
                item.setFlags(
                    QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
                item.setCheckState(QtCore.Qt.Unchecked)
                item.setData(LastStateRole, item.checkState())
                widget.setColumnWidth(0, wCol1)
                widget.setColumnWidth(1, wCol2)
                widget.setColumnWidth(2, wCol3)
                widget.setItem(row, 0, item)

                # insert values into table
                rows = 0
                for tup in list(lists.items()):
                    col = 1
                    for i in tup:
                        cell = QTableWidgetItem(str(i))
                        widget.setItem(rows, col, cell)
                        widget.setRowHeight(rows, 10)
                        cell_align = widget.item(rows, 1)
                        cell_align.setTextAlignment(QtCore.Qt.AlignCenter)
                        col += 1
                    rows += 1
        except Exception as error:
            writelog(error)


def main():
    app = QtWidgets.QApplication(sys.argv)
    # checkbox_style = CheckBoxStyle(app.style())
    # app.setStyle(checkbox_style)
    window = CubeRolesApp()
    window.show()
    app.exec_()


if __name__ == '__main__':
    try:
        fname = os.path.basename(__file__)
        myapp = Singleinstance(fname)
        if myapp.alreadyrunning():
            sys.exit()
        main()
    except Exception as e:
        writelog(e)
    finally:
        sys.exit()


