import time

from selenium.common.exceptions import NoSuchWindowException

from worker.config import config
from selenium import webdriver
from urllib.parse import urlparse


class SeleniumRequest:
    def __init__(self):
        geckodriver = config.get('selenium.geckodriver')
        self.valid = geckodriver is not None
        self.driver = webdriver.Firefox(executable_path=geckodriver)

    def block_get(self, url, cookies):
        self.driver.get(f'https://{urlparse(url).netloc}')
        for key, value in cookies.items():
            self.driver.add_cookie({'name': key, 'value': value})
        self.driver.get(url)
        while True:
            try:
                time.sleep(1)
                self.driver.title  # noqa
            except NoSuchWindowException:
                break
