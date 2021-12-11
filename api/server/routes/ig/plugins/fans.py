from core import IGUser
from server.plugin.plugin import BasePlugin


class IGUserFans(BasePlugin):
    name = 'fans'
    namespace = 'ig'

    def __init__(self, user: IGUser, **kwargs):
        super(IGUserFans, self).__init__(**kwargs)
        self._user = user

    def response(self):
        return {

        }
