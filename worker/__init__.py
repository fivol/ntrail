import asyncio
import sys
import time
from pathlib import Path
sys.path.append(str(Path(__file__).parent.absolute()))

from .engine import Engine
from .parsers.vk.vk import VkMethods
