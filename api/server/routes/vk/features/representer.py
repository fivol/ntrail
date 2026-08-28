from core import VKCommunity, VKUser


class UsersRepresentation:

    @classmethod
    def name(cls, user: dict) -> str:
        return f"{user['first_name']} {user['last_name']}"

    @classmethod
    def url(cls, user) -> str:
        return f'https://vk.com/id{user["id"]}'

    @classmethod
    async def represent(cls, community: VKCommunity):
        data = await community.data()
        return [
            {
                'name': cls.name(user),
                'id': user['id'],
                'url': cls.url(user)
            } for user in data
        ]
