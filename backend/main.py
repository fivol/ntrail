import logging
import warnings
from glbal import logger
from flask import Flask, request, jsonify
from tools import make_json_serializable

from config import VERSION
from selective_query_execute import execute_query

warnings.filterwarnings("ignore")
logger.setLevel(logging.DEBUG)

app = Flask(__name__)
# app.config['RESTPLUS_JSON'] = {'indent': None, 'separators': (',', ':')}


@app.route('/')
def index():
    return VERSION


@app.route('/query/', methods=['get'])
def query_string():
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


if __name__ == '__main__':
    app.debug = True
    app.run()
