import re
from loguru import logger

from server.plugin.plugin import BasePlugin


class VKUserFeatures(BasePlugin):
    name = 'user-features'
    namespace = 'vk'

    def __init__(self, user=None, **kwargs):
        super(VKUserFeatures, self).__init__(**kwargs)
        self._user = user

    @staticmethod
    def _get_sites(site_string):
        site_string = str(site_string)
        regex = r'('
        regex += r'(?:(?:https|http):\/\/)?'
        regex += r'(?:www\.)?'
        regex += r'(?:(?:[a-z0-9][a-z0-9-]{0,61}[a-z0-9]\.)+)'
        regex += r'(?:[a-z]{2,6})'
        regex += r'(?:(?:\/[a-z0-9_\-.]+)*)'
        regex += r'(?:\?[^;\s]+)?'
        regex += r')'
        urls = re.findall(regex, site_string)

        sites = []
        for inst_username in re.findall(r'\W@([a-zA-Z0-9_.]+)', site_string):
            sites.append(('instagram', 'https://www.instagram.com/{}/'.format(inst_username)))

        for site in urls:
            try:
                if (site.startswith('www') or '//www.' in site) and len(site.split('.')) <= 2:
                    continue

                if not site.startswith('http://') and not site.startswith('https://'):
                    site = 'https://' + site

                host = site.split('//')[1]
                if host.startswith('www.'):
                    host = host[4:]

                host_name = host.split('/')[0].split('.')[-2]
                sites.append((host_name, site))
            except:
                logger.exception('Fail to parse site: {}', site)

        return sites

    def _get_key_words(self):
        user = self._user
        data = user.data()
        site_string = ' '.join([str(item) for key, item in data if not key.startswith('photo')])
        sites = self._get_sites(site_string)
        sites_username = []
        for host, site in sites:
            try:
                if site.endswith('/'):
                    site = site[:-1]
                path_items = site.split('//')[1].split('/')
                if len(path_items) >= 2:
                    sites_username.append(path_items[-1])
            except:
                logger.exception('Fail to get username from site: {}', site)

        key_words = [
            self.name,
            data.get('first_name', None),
            data.get('last_name', None),
            data.get('screen_name', None),
            data.get('skype', None),
            data.get('livejournal', None),
            data.get('instagram', None),
            data.get('twitter', None),
            data.get('facebook', None),
            data.get('maiden_name', None),
            data.get('nickname', None),
            *sites_username
        ]
        key_words = list(filter(lambda x: bool(x), key_words))
        return key_words

    def response(self) -> dict:
        return {
            'keywords': self._get_key_words()
        }
