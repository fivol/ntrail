
class InitializerModel:

    def _init(self, props: dict):
        for key, value in props.items():
            if hasattr(self, key) and getattr(self, key) is None:
                setattr(self, key, value)
