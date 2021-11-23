import sys
import os
import worker.config

import logging

logging.getLogger(__name__)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))


from worker.parsers.vk.vk import VkMethods
from worker.parsers.ig.ig import IgMethods
from worker.engine import Engine
