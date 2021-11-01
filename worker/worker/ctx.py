from worker.tools import assert_imported_once


# Singleton app context
class WorkerContext(dict):

    def set_default(self, name, value):
        if name not in self:
            self[name] = value

    def __getattr__(self, item):
        return self[item]

    def __setattr__(self, key, value):
        self[key] = value


assert_imported_once()

__ctx = WorkerContext()


def get_context():
    return __ctx
