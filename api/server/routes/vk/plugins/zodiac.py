from datetime import datetime

from core import VKUser
from server.plugin.plugin import BasePlugin


class UserZodiacPlugin(BasePlugin):
    name = 'user-zodiac'

    def __init__(self, user: VKUser, **kwargs):
        super(UserZodiacPlugin, self).__init__(**kwargs)
        self._user = user

    zodiac_signs = [
        ['21.03-19.04', 'Овен', '♈'],
        ['20.04-20.05', 'Телец', '♉'],
        ['21.05-20.06', 'Близнецы', '♊'],
        ['21.06-22.07', 'Рак', '♋'],
        ['23.07-22.08', 'Лев', '♌'],
        ['23.08-22.09', 'Дева', '♍'],
        ['23.09-22.10', 'Весы', '♎'],
        ['23.10-21.11', 'Скорпион', '♏'],
        ['22.11-21.12', 'Стрелец', '♐'],
        ['22.12-20.01', 'Козерог', '♑'],
        ['21.01-18.02', 'Водолей', '♒'],
        ['19.02-20.03', 'Рыбы', '♓'],
    ]

    zodiac_sign = {}

    @classmethod
    def get_sign(cls, i):
        return (cls.zodiac_signs + cls.zodiac_signs)[i]

    @classmethod
    def _get_dd_mm(cls, dm):
        d, m = dm.split('.')
        return datetime(
            day=int(d),
            month=int(m),
            year=2000
        ).strftime("%d.%m")

    @classmethod
    def _calculate_zodiac_dict(cls):
        i = 9
        for month in range(1, 12 + 1):
            for day in range(1, 31 + 1):
                try:
                    date = cls._get_dd_mm(f'{day}.{month}')
                except ValueError:
                    continue
                sign_date, sign, emoji = cls.get_sign(i)
                ends = sign_date.split('-')[1]
                cls.zodiac_sign[date] = (sign, emoji)
                if ends == date:
                    i += 1

    @classmethod
    def _date_to_zodiac_sign(cls, dm):
        return cls.zodiac_sign[cls._get_dd_mm(dm)]

    async def response(self) -> dict:
        bdate = (await self._user.data()).get('bdate')
        if not bdate:
            return {}
        dd_mm = '.'.join(bdate.split('.')[:2])
        name, emoji = self._date_to_zodiac_sign(dd_mm)
        return {
            'name': name,
            'emoji': emoji
        }

UserZodiacPlugin._calculate_zodiac_dict() # noqa
