import asyncio
import json
import logging

from worker.config import config

logger = logging.getLogger('execute')


class ExecuteRequestPool:
    """
    https://vk.com/dev/execute
    """

    def __init__(self):
        self._execute_epoch = 0
        self._execute_results = {}
        self._executable_pool = []
        self._execute_length = 0

    @staticmethod
    def _gen_execute_code(items) -> str:
        """Item be like
        [('users.get', {'user_id': 123})]
        """
        commands = [
            f'API.{method_name}({json.dumps(kwargs, separators=(",", ":"))})'
            for method_name, kwargs in items
        ]
        return f'return [{",".join(commands)}];'

    async def _run_execute_pool(self, only_user_access=False):
        from worker import VkMethods

        # Label results as waiting
        if not self._executable_pool:
            raise IndexError
        logger.debug('Run execute pool %s', len(self._executable_pool))
        code = self._gen_execute_code(self._executable_pool)
        execute_coro = VkMethods.execute(code, only_user_access=only_user_access)
        execute_task = asyncio.create_task(execute_coro)

        self._execute_results[self._execute_epoch] = execute_task
        self._execute_epoch += 1
        await self._reset_pool()

    async def _reset_pool(self):
        self._executable_pool = []
        self._execute_length = 0

    async def try_use_execute(self, method, kwargs, only_user_access=False):
        """Tries to add request to execute pool, if success returns result, else None"""
        cmd_idx = len(self._executable_pool)
        curr_epoch = self._execute_epoch
        cmd_length = len(json.dumps((method, kwargs)))

        if cmd_length > config.vk.EXECUTE_MAX_LENGTH:
            logger.warning('Too long command to use execute command: %s', cmd_length)
            await self._reset_pool()
            return None

        self._executable_pool.append((method, kwargs))
        self._execute_length += cmd_length
        if len(self._executable_pool) == config.vk.EXECUTE_QUERIES_BUNCH_COUNT or \
                self._execute_length > config.vk.EXECUTE_MAX_LENGTH:
            # TODO Make second condition correct
            await self._run_execute_pool(only_user_access)

        # Very important. We should return control to collect many queries in pool in async
        await asyncio.sleep(0)
        if len(self._executable_pool) < 15:
            await asyncio.sleep(0.001)
        if self._execute_epoch == curr_epoch and len(self._executable_pool) >= 3:
            await self._run_execute_pool(only_user_access)
        results = self._execute_results.get(curr_epoch, None)

        if results is None:
            await self._reset_pool()
            return None

        if isinstance(results, asyncio.Task):
            real_results = await results
            self._execute_results[curr_epoch] = [real_results, len(real_results)]

        results, remain_count = self._execute_results[curr_epoch]
        assert isinstance(results, list)
        if results[0] is False:
            logger.warning('Execute query returns False')
            raise Warning('It seems, execute query failed')
        self._execute_results[curr_epoch][1] -= 1
        result = results[cmd_idx]
        if not self._execute_results[curr_epoch][1]:
            del self._execute_results[curr_epoch]
        return result
