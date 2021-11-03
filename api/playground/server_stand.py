import logging


from server.types import ResponseVerbose


class ServerStand:
    def __init__(self, debug=True):
        if not debug:
            logging.getLogger().setLevel(logging.ERROR)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def run(self, options, verbose=ResponseVerbose.normal, **kwargs):
        assert isinstance(options, list)
        return
