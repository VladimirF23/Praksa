class ConnectionException(Exception):
    def __init__(self, message="A connection error occurred"):
        super().__init__(message)

class DuplicateKeyException(Exception):
    def __init__(self, message="A duplicate key (e.g., username) was found in the database."):
        super().__init__(message)

class IlegalValuesException(Exception):
    def __init__(self, message="Ilegal Values"):
        super().__init__(message)

class NoAuthorizationException(Exception):
    def __init__(self, message="No Authorization !"):
        super().__init__(message)

class NotAcceptedException(Exception):
    """
    Exception raised when an action cannot be completed because the user's registration
    or request has not been accepted/approved.
    """
    def __init__(self, message="The requested action cannot be completed as the registration or request is not accepted."):
        super().__init__(message)
        
class NotFoundException(Exception):
    def __init__(self, message="Not found."):
        super().__init__(message)
