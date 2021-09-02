#!/usr/bin/env python
# coding:utf-8
"""
Author : Vitaliy Zubriichuk
Contact : v@zubr.kiev.ua
Time    : 31.08.2021 13:13
"""
import getpass
import os
import sys

from PyQt5 import QtWidgets
from PyQt5.Qt import QHBoxLayout
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import *

import access
import app_filial as appf
from db_connect import DBConnect
from log_error import writelog
from singleinstance import Singleinstance
from gui.welcomeWindow import Ui_welcomeWindow

db_info = access.conn_info
sql = DBConnect(server=db_info.get('Server'),
                db=db_info.get('DB'),
                uid=db_info.get('UID'),
                pwd=db_info.get('PWD'))


class RestartRequiredError(Exception):
    """ Exception raised if restart is required.

    Attributes:
        expression - input expression in which the error occurred;
        message - explanation of the error.
    """

    def __init__(self, expression,
                 message='Необходима перезагрузка приложения'):
        self.expression = expression
        self.message = message
        super().__init__(self.expression, self.message)


class NetworkError(QWidget):
    def __init__(self):
        super().__init__()
        QMessageBox.critical(self, 'Ошибка cети',
                             'Возникла общая ошибка сети.\n'
                             'Перезапустите приложение',
                             QMessageBox.Ok, QMessageBox.Ok)


class UnexpectedError(QWidget):
    def __init__(self, *args):
        super().__init__()
        QMessageBox.critical(self, 'Непредвиденное исключение',
                             'Возникло непредвиденное исключение\n' + '\n'.join(
                                 map(str, args)),
                             QMessageBox.Ok, QMessageBox.Ok)


class WelcomeWindow(QtWidgets.QMainWindow, Ui_welcomeWindow):
    def __init__(self):
        super().__init__()
        self.app_filial = appf.FilialApp()
        self.setupUi(self)  # Это нужно для инициализации нашего дизайна
        # нужный костыль для вывода иконки на splash screen
        hbox = QHBoxLayout(self)
        hbox.addWidget(self.splash_label)
        self.setLayout(hbox)

        self.report_id = 0
        self.pushButtonExit.clicked.connect(QtWidgets.qApp.quit)
        self.pushButtonRun.clicked.connect(self.choose_app)

        # loading list of reports
        try:
            with sql:
                self.report_list = dict(sql.get_apps())
                for key, values in self.report_list.items():
                    self.apps_dropdown.addItem(values)
        except Exception as error:
            writelog(error)

    def choose_app(self):
        for k, v in self.report_list.items():
            if v == self.apps_dropdown.currentText():
                self.report_id = k
                if self.report_id == 1:
                    self.openApp(self.report_id)

    def openApp(self, app):
        if app == 1:
            self.hide()
            self.app_filial.show()
            self.app_filial.raise_()

def welcome_Window():
    splash = QtWidgets.QApplication(sys.argv)
    splash_window = WelcomeWindow()
    splash_window.setWindowFlags(Qt.SplashScreen | Qt.FramelessWindowHint)
    splash_window.show()
    splash.exec_()

def main():
    UserLogin = getpass.getuser()
    # Check connection to db and permission to work with app



    try:
        welcome_Window()
    except Exception as e:
        writelog(e)



if __name__ == '__main__':
    try:
        fname = os.path.basename(__file__)
        myapp = Singleinstance(fname)
        if myapp.alreadyrunning():
            sys.exit()
        main()
    except RestartRequiredError as e:
        pass
        # tkp.RestartRequiredAfterUpdateError()
    except Exception as e:
        writelog(e)
    finally:
        sys.exit()
