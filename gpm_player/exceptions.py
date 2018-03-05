class BasePlayerException(Exception):
    pass


class LoginFailure(BasePlayerException):
    def __str__(self):
        return 'Credentials weren\'t accepted.'


class PlayerExitException(BasePlayerException):
    pass


class StoredTrackError(BasePlayerException):
    def __str__(self):
        return 'Track does not exist in store.'
