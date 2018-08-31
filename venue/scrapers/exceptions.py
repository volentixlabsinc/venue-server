class ProfileDoesNotExist(Exception):

    def __init__(self, message, info={}):
            self.message = message
            self.info = info
            if 'response_text' in self.info.keys():
                if self.info['response_text'] is None:
                    self.info['response_text'] = ''


class ScraperError(Exception):

    def __init__(self, message, info={}):
            self.message = message
            self.info = info
            if 'response_text' in self.info.keys():
                if self.info['response_text'] is None:
                    self.info['response_text'] = ''
