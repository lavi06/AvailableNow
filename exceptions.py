class InvalidCredentialsError(Exception):
    """Exception raised for invalid login credentials."""

    def __init__(self, message="Invalid username or password."):
        self.message = message
        super().__init__(self.message)


class UserException(Exception):
    """Exception raised when there is an error with user login"""

    def __init__(self, message="User operation Failed"):
        self.message = message
        super().__init__(self.message)


class DbException(Exception):
    """Exception raised when there is an error with database connection and database operation"""

    def __init__(self, message="Database operation failed"):
        self.message = message
        super().__init__(self.message)


class AlreadyScheduleException(DbException):
    def __init__(self, message="found already a schedule"):
        self.message = message
        super().__init__(self.message)


class OperationalException(Exception):

    def __init__(self, message="Failed to perform operation/function"):
        self.message = message
        super().__init__(self.message)
