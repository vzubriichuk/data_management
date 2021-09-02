# -*- coding: utf-8 -*-
"""
Created on Thu Jul  4 15:15:57 2019

@author: v.shkaberda
"""
from win32event import CreateMutex
from win32api import CloseHandle, GetLastError
from winerror import ERROR_ALREADY_EXISTS

class Singleinstance:
    """ Limits application to single instance. """
    def __init__(self, mutexname):
        self.mutexname = "{}_{{D0E858DF-985E-4907-B7FB-8D732C3FC3B9}}".format(mutexname)
        self.mutex = CreateMutex(None, False, self.mutexname)
        self.lasterror = GetLastError()

    def alreadyrunning(self):
        return (self.lasterror == ERROR_ALREADY_EXISTS)

    def __del__(self):
        if self.mutex:
            CloseHandle(self.mutex)