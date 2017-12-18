import base64
import hashlib
from enum import Enum
import datetime
import time

from django.conf import settings
import django.db


class EjudgeDatabase:
    def __init__(self):
        self.connection = django.db.connections['ejudge']

    @staticmethod
    def _dict_fetchall(cursor, constructor=None):
        """Returns all rows from a cursor as a dict or object"""
        if constructor is None:
            def constructor(**kwargs):
                return kwargs
        desc = cursor.description
        return [
            constructor(**dict(zip([col[0] for col in desc], row)))
            for row in cursor.fetchall()
            ]

    @staticmethod
    # TODO: copy-paste, see previous method
    def _dict_fetchone(cursor, constructor=None):
        """Returns all rows from a cursor as a dict or object"""
        if constructor is None:
            def constructor(**kwargs):
                return kwargs
        desc = cursor.description
        row = cursor.fetchone()
        if row is None:
            return None
        return constructor(**dict(zip([col[0] for col in desc], row)))

    def get_runs(self, before_time=None):
        if before_time is None:
            before_time = datetime.datetime.now()
        contest_id = settings.EJUDGE_CONTEST_ID
        cursor = self.connection.cursor()
        cursor.execute('SELECT *, UNIX_TIMESTAMP(create_time) AS create_time_unix FROM runs WHERE contest_id = %s AND UNIX_TIMESTAMP(create_time) < %s',
                       [contest_id, time.mktime(before_time.timetuple())])
        return self._dict_fetchall(cursor, Run)

    def get_runs_by_user(self, user):
        ejudge_user_id = user.info.ejudge_user_id

        contest_id = settings.EJUDGE_CONTEST_ID
        cursor = self.connection.cursor()
        cursor.execute('SELECT *, UNIX_TIMESTAMP(create_time) AS create_time_unix FROM runs WHERE contest_id = %s AND user_id = %s',
                       [contest_id, ejudge_user_id])
        return self._dict_fetchall(cursor, Run)

    def is_login_and_password_correct(self, login, password):
        user = self.get_user_by_login(login)

        if user is None:
            return False

        # Internal ejudge password storing: 0 for plain text, 1 for base64, 2 for sha1
        # For details see https://github.com/blackav/ejudge/blob/master/include/ejudge/userlist.h
        #
        if user['pwdmethod'] == 0:
            return user['password'] == password
        elif user['pwdmethod'] == 1:
            return user['password'] == base64.b64encode(password.encode()).decode()
        elif user['pwdmethod'] == 2:
            return user['password'] == hashlib.sha1(password.encode()).hexdigest()
        else:
            raise Exception('Unsupported pwdmethod: %s' % str(user['pwdmethod']))

    def get_user_by_login(self, login):
        cursor = self.connection.cursor()
        cursor.execute('SELECT * FROM logins WHERE login = %s', [login])
        return self._dict_fetchone(cursor)


class Run:
    def __init__(self, run_id, user_id, prob_id, lang_id, status, create_time_unix, **kwargs):
        self.id = run_id
        self.user_id = user_id
        self.problem_id = prob_id
        self.language_id = lang_id
        self.status = RunStatus(status)
        self.time = create_time_unix


class RunStatus(Enum):
    OK = 0
    COMPILATION_ERROR = 1
    RUN_TIME_ERROR = 2
    TIME_LIMIT_EXCEEDED = 3
    PRESENTATION_ERROR = 4
    WRONG_ANSWER = 5
    CHECK_FAILED = 6
    PARTIAL_SOLUTION = 7
    ACCEPTED_FOR_TESTING = 8
    IGNORED = 9
    DISQUALIFIED = 10
    PENDING = 11
    MEMORY_LIMIT_EXCEEDED = 12
    SECURITY_VIOLATION = 13
    STYLE_VIOLATION = 14
    WALL_TIME_LIMIT_EXCEEDED = 15
    PENDING_REVIEW = 16
    REJECTED = 17
    SKIPPED = 18
    FULL_REJUDGE = 95
    RUNNING = 96
    COMPILED = 97
    COMPILING = 98
    AVAILABLE_FOR_TESTING = 99
    REJUDGE = 99
    EMPTY_RECORD = 22
    VIRTUAL_START = 20
    VIRTUAL_STOP = 21