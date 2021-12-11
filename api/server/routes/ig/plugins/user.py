from core import IGUser
from server.exceptions import WrongInputError
from server.plugin.plugin import InputPlugin, BasePlugin
from worker.parsers.exceptions import AccessApiException


class IGUserInput(InputPlugin):
    name = 'user'
    namespace = 'ig'

    @classmethod
    async def read(cls, user: str, **kwargs) -> dict:
        try:
            return {
                'user': await IGUser.create(user)
            }
        except AccessApiException:
            raise WrongInputError('Such user does not exists')


class IGUserPlugin(BasePlugin):
    name = 'user'
    namespace = 'ig'

    def __init__(self, user: IGUser, **kwargs):
        super(IGUserPlugin, self).__init__(**kwargs)
        self._user = user
        self._data = None

    async def data(self):
        self._data = await self._user.data()
        self._data = {
            key: value for key, value in self._data.items() if not isinstance(value, dict)
        }
        return self._data

    def response(self):
        return {
            'name': self._user.full_name
        }
