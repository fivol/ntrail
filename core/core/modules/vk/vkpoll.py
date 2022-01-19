from core.module.layers import data_method_decorator
from core.module.single_entity import SingleEntity
from pycommon.decors import cache_method_ignore_args
from worker import VKMethods


class VKPoll(SingleEntity):
    def __init__(self, item=None, poll_id=None, owner_id=None, **kwargs):
        self.id = poll_id
        self.owner_id = owner_id
        self.created = None
        self.question = None
        self.votes = None
        self.anonymous = None
        self.multiple = None
        self.closed = None
        self.author_id = None
        self.answers = None
        super(VKPoll, self).__init__(item, **kwargs)

    @data_method_decorator
    async def data(self):
        return await VKMethods.poll(poll_id=self.id, owner_id=self.owner_id)

    def valid(self):
        return bool(self.id)

    def status(self):
        return None

    @cache_method_ignore_args
    async def get_votes(self):
        answers = {
            answer['id']: answer['text'] for answer in self.answers
        }
        votes = await VKMethods.poll_votes(owner_id=self.owner_id, poll_id=self.id, answer_ids=list(answers.keys()))
        return {
            answers[vote['answer_id']]: vote['users'] for vote in votes
        }
