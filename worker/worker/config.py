from bestconfig import Config

config = Config('local-config.yml', exclude=['env_file'])
assert config.contains('DEBUG'), 'Probably you miss specify config.yml file with necessary variables'
