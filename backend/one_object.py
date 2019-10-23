from baseapi import BaseAPI


class OneObject(BaseAPI):
    def print(self, extra_data=''):
        if not self.valid:
            print('This object is not valid')
            return
        name = f'{self.pk} {self.name} {extra_data}'
        name = name + ' ' * max(32 - len(name), 1)
        print(f'{name} {self.url}')

    def __hash__(self):
        return hash(self.pk)

    def __eq__(self, other):
        return hash(other) == hash(self)
