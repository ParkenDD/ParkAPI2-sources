"""
Copyright 2023 binary butterfly GmbH
Use of this source code is governed by an MIT-style license that can be found in the LICENSE.txt.
"""


class ImportException(Exception):
    uid: str
    message: str

    def __init__(self, uid: str, message: str):
        self.uid = uid
        self.message = message

    def __repr__(self):
        return f'{self.__class__.__name__} {self.uid}: {self.message}'


class ImportSourceException(ImportException):
    pass


class ImportParkingSiteException(ImportException):
    pass
