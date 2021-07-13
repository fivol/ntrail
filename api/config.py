from bestconfig import Config

config = Config()

from core.call_worker.api_query import APIQueries

assert config.get('MY_VK_ACCESS_TOKEN')
APIQueries.add_default_env({
    'access_token': config.get('MY_VK_ACCESS_TOKEN')
})
