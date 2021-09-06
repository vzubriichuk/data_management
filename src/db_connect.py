#!/usr/bin/env python
# coding:utf-8
"""
Author : Vitaliy Zubriichuk
Contact : v@zubr.kiev.ua
Time    : 30.04.2021 9:28
"""
from functools import wraps
import pyodbc
from pyodbc import Error as SQLError
from log_error import writelog


class Error(Exception):
    """ Exception raised if error has detected.
    Attributes:
        expression - input expression in which the error occurred;
    """

    def __init__(self, expression):
        self.expression = expression
        super().__init__(self.expression)


class DBConnect(object):
    def __init__(self, server, db, uid=None, pwd=None):
        self._server = server
        self._db = db
        self._uid = uid
        self._pwd = pwd

    def __enter__(self):
        # Connection properties
        conn_str = (
            f'Driver={{SQL Server}};'
            f'Server={self._server};'
            f'Database={self._db};'
        )
        if self._uid:
            conn_str += f'uid={self._uid};pwd={self._pwd}'
        else:
            conn_str += 'Trusted_Connection=yes;'
        self.__db = pyodbc.connect(conn_str)
        self.__cursor = self.__db.cursor()
        return self

    def __exit__(self, type, value, traceback):
        self.__db.close()

    def get_apps(self):
        """ Check user permission.
            If access permitted returns True, otherwise None.
        """
        query = ''' 
            SELECT idParamsLines, ValueDescription
            FROM  LogisticFinance.dbo.GlobalParamsLines
            WHERE idParams = 13
        '''
        self.__cursor.execute(query)
        return self.__cursor.fetchall()

    """
    Блок функций приложения "Управление филиалами в отчетах"
    """
    def get_reports(self):
        """ Check user permission.
            If access permitted returns True, otherwise None.
        """
        query = ''' 
            SELECT id, ReportName
            FROM reporting.fcp@report_list
            ORDER  BY ReportName
        '''
        self.__cursor.execute(query)
        return self.__cursor.fetchall()

    def get_report_info(self, report_id):
        query = ''' 
            exec [reporting].[fcp@get_current_info] @ReportID = ?
        '''
        self.__cursor.execute(query, report_id)
        return self.__cursor.fetchall()

    def get_all_filials(self, report_id):
        query = ''' 
            exec [reporting].[fcp@get_filials] @ReportID = ?
        '''
        self.__cursor.execute(query, report_id)
        return self.__cursor.fetchall()

    def remove_filials(self, report_id, filials, user):
        query = ''' 
            exec reporting.fcp@filials_remove @ReportID = ?,
                                              @Filials = ?,
                                              @User = ?
        '''
        try:
            self.__cursor.execute(query, report_id, filials, user)
            status = self.__cursor.fetchone()
            self.__db.commit()
            return status
        except pyodbc.ProgrammingError as error:
            writelog(error)
            status = 0
            return status

    def add_filials(self, report_id, filials, user):
        query = ''' 
            exec reporting.fcp@filials_add @ReportID = ?,
                                           @Filials = ?,
                                           @User = ?
                                            
        '''
        try:
            self.__cursor.execute(query, report_id, filials, user)
            status = self.__cursor.fetchone()
            self.__db.commit()
            return status
        except pyodbc.ProgrammingError as error:
            writelog(error)
            status = 0
            return status

    """
    Блок функций модуля "Управления ролями пользователей в кубах"
    """
    def get_users(self):
        query = '''
            select [cub.People.peopleLogin], [cub.People.peopleFullName]
            from [DBMS_S31].[MasterData].[dbo].[dim_Staff] s
            where 1=1
            and [cub.Staff.isWork] = 1
            and [cub.Businesses.topLevelBusinessId] in ( 80  )
            and [cub.People.peopleLogin] is not NULL
        '''
        self.__cursor.execute(query)
        return self.__cursor.fetchall()

    def get_user_info(self, UserName):
        query = '''
            exec reporting.proc_dm@get_user_info @UserName = ?
        '''
        self.__cursor.execute(query, UserName)
        return self.__cursor.fetchone()

    def get_list_active_cubes(self, userLogin):
        query = '''
            exec [reporting].[proc_dm@get_active_cubes] @UserName = ?
        '''
        self.__cursor.execute(query, userLogin)
        return self.__cursor.fetchall()

    def get_list_cubes(self, userLogin):
        query = '''
            exec [reporting].[proc_dm@get_available_cubes] @UserName = ?
        '''
        self.__cursor.execute(query, userLogin)
        return self.__cursor.fetchall()

    def add_roles_to_user(self, userLogin, cubeID, add_type):
        query = ''' 
            exec [reporting].[proc_dm@user_add_role] @userLogin = ?,
                                                     @cubeID = ?,
                                                     @add_type = ?
                                            
        '''
        try:
            self.__cursor.execute(query, userLogin, cubeID, add_type)
            status = self.__cursor.fetchone()
            self.__db.commit()
            return status
        except pyodbc.ProgrammingError as error:
            writelog(error)
            status = 0
            return status
