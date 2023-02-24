class AppError(RuntimeError):
    def __init__(self, application):
        self.app = application

class AppNotInstalledError(AppError):
    pass

class AppNotRunningError(AppError):
    pass
