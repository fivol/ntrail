from flask import request, jsonify, Response, make_response

from auth.db import AuthDB
from auth.vk.logic import VKAuthorization
from exceptions import HandledException
from glbal import logger
from ntmodule.tools import make_json_serializable
from selective_query_execute import execute_query
from flask import g


def api_request(func):
    """Proxy для любого запроса. Отвечает за авторизацию пользователя"""

    def wrapper(*args, **kwargs):
        # Check input token
        token_header_name = 'authorization'
        token = request.headers.get(token_header_name)
        print('token', token)

        if not token:
            print('have not token')
            # Ситуация, когда запрос был сделан не с фронта
            # От туда приходит undefined если токена нету

            # user = AuthDB.create_user()
            # token = user.token
        else:
            user = AuthDB.get_user(token)
            # Если токен невалиден
            if not user:
                print('Wrong token, create new user')
                user = AuthDB.create_user()
            else:
                if user.depends_on:
                    user = AuthDB.get_user_by_id(user.depends_on)
            token = user.token

            # g - global dict over all request
            g.user = user
        g.token = token

        response = func(*args, **kwargs)
        if isinstance(response, dict):
            response = jsonify(response)
        if not isinstance(response, Response):
            response = make_response(response)

        # Set auth token
        response.headers[token_header_name] = g.token
        headers = {
            'Access-Control-Allow-Headers': 'authorization'
        }
        response.headers.extend(headers)
        response.headers.add_header('Access-Control-Expose-Headers', 'authorization')
        return response

    return wrapper


class APIData:

    @classmethod
    @api_request
    def query_string(cls):
        try:
            q_string = request.args.get('q')
            if q_string:
                response = execute_query(q_string)
            else:
                response = {
                    'code': 400,
                    'error': 'Неверный формат запроса. Не найден параметр q в GET зарпосе'
                }

            response = make_json_serializable(response)
            if isinstance(response, dict):
                if 'code' not in response:
                    response['code'] = 200
                if 'error' not in response:
                    response['error'] = ''
            else:
                response = {
                    'code': 500,
                    'error': f'Неверный тип возвращаемых данных ({type(response)}). Ошибка сервера'
                }

        except:
            logger.exception('Unknown api error')
            response = {
                'code': 520,
                'error': f'Неизвестная ошибка сервера. Напишите в поддержку для оперативного исправления'
            }
        response_code = response['code']

        response = jsonify(response)
        response.headers.add("Access-Control-Allow-Origin", "*")

        return response, response_code


class APIAuth:

    @classmethod
    @api_request
    def init(cls):
        """Before authentication
        Target is to accept token (chack api_request)
        """
        return 'OK'

    @classmethod
    @api_request
    def auth_vk(cls):
        """Authorization Code Flow для получения ключа доступа пользователя
        https://vk.com/dev/authcode_flow_user
        Сюда будет приходить токен при авторизации пользователя через вк
        return: при успешной авторизации, возвращается значение status: 'ok',
        в противном случае status: 'error'
        """
        logger.info('Auth query')
        try:
            code = request.args.get('code')
            error = request.args.get('error')
            error_description = request.args.get('error_description')
            if error:
                logger.warning('Пришел запрос с ошибкой на /auth/vk/. err: %s, описание: %s', error, error_description)
                raise HandledException

            if not code:
                logger.error("Код не пришел на запрос /auth/vk/")
                raise HandledException

            user_token = request.args.get('state')

            VKAuthorization.vk_auth(user_token, code)
        except HandledException:
            pass
        except:
            logger.exception('Unknown exception in vk auth')

        return VKAuthorization.close_window_response()

    @classmethod
    @api_request
    def check(cls):
        """После того, как уже закрыто окно авторизации через вк,
        фронт делает запрос на этот endpoint. В ответ получает статус
        успешно или нет и прикрепленный херед если отсутствовал
        Выставляет новый token если у текущего есть depends_on поле
        """
        authorized = VKAuthorization.check_auth(g.user.id)
        if authorized:
            return {
                'status': 'authorized'
            }
        return {
            'status': 'unauthorized'
        }
