import logging
import warnings

from auth.vk.logic import VKAuthorization
from exceptions import HandledException
from glbal import logger
from flask import Flask, request, jsonify
from ntmodule.tools import make_json_serializable

from config import VERSION
from selective_query_execute import execute_query
from flask_cors import CORS
import os

warnings.filterwarnings("ignore")
logger.setLevel(logging.DEBUG)

app = Flask(__name__)
CORS(app)

# After app init!
from api import *


@app.route('/')
def index():
    return VERSION


@app.route('/auth/vk/')
def auth_vk():
    return APIAuth.auth_vk()


@app.route('/auth/init/')
def auth_init_query():
    return APIAuth.init()


@app.route('/auth/vk/check/')
def auth_vk_check():
    return APIAuth.check()


@app.route('/feedback/', methods=['post'])
def feedback():
    print('FEEDBACK JSON', request.get_json())
    return 'OK'


@app.route('/query/', methods=['get'])
def query_string():
    return APIData.query_string()


if __name__ == '__main__':
    logger.info('Run main, version: %s', VERSION)
    if os.environ.get('ENV', 'UNKNOWN') == 'DOCKER':
        logger.info('DOCKER ENVIRONMENT')
        # Не менять этот порт, его использует nginx
        app.run(host='0.0.0.0', port='5000', debug=False)
    else:
        logger.info('LOCAL ENVIRONMENT')
        app.run(host='localhost', port='5000', debug=True)

    logger.info('STOP')
