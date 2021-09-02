#!/usr/bin/env python
# coding:utf-8
"""
Author : Vitaliy Zubriichuk
Contact : v@zubr.kiev.ua
Time    : 31.08.2021 14:18
"""


import os
import sys
import zlib
from contextlib import suppress
from shutil import copy2
from time import sleep

from _version import upd_path
from log_error import writelog
from main import NetworkError, UnexpectedError
from singleinstance import Singleinstance

SOURCE = zlib.decompress(upd_path).decode()
ALREADY_UPDATED = []


def update_files(main_path, path, directories, files):
    # specify path in current working directory
    relative_path = path.replace(main_path, '.')
    for file in files:
        if (relative_path, file) not in ALREADY_UPDATED:
            copy2(os.path.join(path, file), relative_path)
            ALREADY_UPDATED.append((relative_path, file))
    # create new directory if needed
    with suppress(FileExistsError):
        for directory in directories:
            os.mkdir(os.path.join(relative_path, directory))


def versioned(fname):
    """ Function to convert folder name into version ('1.2.13' -> (1, 2, 13)).
    """
    try:
        return tuple(map(int, fname.split('.')))
    except ValueError:
        return (0,)


def check_updates_and_run_app():
    # Extract names of all directories. Name of directory means version of app.
    app_versions = next(os.walk(SOURCE))[1]
    # Determine current version of application
    try:
        with open('contracts.inf', 'r') as f:
            version_info = f.readline()
            version_info = versioned(version_info)
    except FileNotFoundError:
        from _version import version_info
    # Check all new versions and sort in descending order
    new_versions = sorted((x for x in app_versions if versioned(x) > version_info),
                          key=versioned,
                          reverse=True)
    for v in new_versions:
        path = os.path.join(SOURCE, v)
        for data in os.walk(path):
            update_files(path, *data)
    # Update version in contracts.inf
    if new_versions:
        with open('contracts.inf', 'w') as f:
            f.write(new_versions[0])
    # Run main executable
    os.startfile("contracts.exe")
    sleep(5)


def main():
    # Create splash screen
    exception_handlers = {'NetworkError': NetworkError,
                          'UnexpectedError': UnexpectedError}
    root = SplashScreen(func=check_updates_and_run_app,
                        exception_handlers=exception_handlers)
    root.overrideredirect(True)

    logo = PhotoImage(file='resources/paper.png')
    logo_label = Label(root, image=logo)
    logo_label.pack(side='top', pady=40)

    copyright_label = Label(root, text='© 2020 Офис контролинга логистики')
    copyright_label.pack(side='bottom', pady=5)

    label = Label(root,
                  text='Выполняется поиск обновлений и запуск приложения...')
    label.pack(expand='yes')

    root.after(300, root.task)
    root.mainloop()


if __name__ == '__main__':
    try:
        fname = os.path.basename(__file__)
        myapp = Singleinstance(fname)
        if myapp.aleradyrunning():
            sys.exit()
        main()
    except Exception as e:
        writelog(e)
        print(e)
    finally:
        sys.exit()