from worker.instagramscraper.exception.instagram_exception import InstagramException


class InstagramNotFoundException(InstagramException):
    def __init__(self, message="", code=404):
        super().__init__(f'{message}, Code:{code}')
