class ProfileDoesNotExist(Exception):

    def __init__(self, message, info={}):
            self.message = message
            self.info = info


class ScraperError(Exception):

    def __init__(self, message, info={}):
            self.message = message
            self.info = info
