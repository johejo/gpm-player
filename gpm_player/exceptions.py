class BasePlayerException(Exception):
    pass


class StationPlayerError(BasePlayerException):
    pass


class LoginFailure(StationPlayerError):
    def __str__(self):
        return 'Credentials weren\'t accepted.'
