from auth.db import AuthDB
from auth.vk.db import VKAuthDB
from auth.vk.native import VKNativeAuthFlow
from exceptions import HandledException, DBException
from glbal import logger
import typing as t


class VKAuthorization:
    @classmethod
    def vk_auth(cls, token: str, code: str) -> t.Optional[int]:
        """Создает новую запись в бд с токеном авторизации пользователя
        Returns original user.id if vk authentication already exists"""

        user = AuthDB.get_user(token)
        if not user:
            user = AuthDB.create_user()

        try:
            token = VKNativeAuthFlow.get_access_token(code)
            try:
                VKAuthDB.auth_vk(user.id, token)
                logger.info('Success auth new vk user')
            except DBException:
                logger.warning('User already exists in authorization data base')
                original_user = VKAuthDB.get_user(token)
                if not original_user:
                    raise Exception('Не найден пользователь')

                AuthDB.set_dependencies(user, original_user.id)
                return user.id

        except HandledException:
            pass
        except:
            logger.exception('Unknown exception in vk auth')

    @classmethod
    def check_auth(cls, user_id: int):
        return VKAuthDB.check_auth(user_id)

    @staticmethod
    def close_window_response():
        """Возвращает JS код, который будет закрывать окно
        Все действия по авторизации уже совершены. Клиенту осталось только
        отправить API запрос для проверки статуса и получения токена"""

        return """<script type="text/javascript">
                window.open('','_parent',''); 
                window.close();
                </script>
                """
