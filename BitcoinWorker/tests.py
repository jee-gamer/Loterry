import asyncio
import unittest

import redis.asyncio as redis

redis_client = redis.Redis(host='localhost', port=6379, db=0)
pubsub = redis_client.pubsub()


async def listen_redis():

    await pubsub.subscribe('blocks')
    async for message in pubsub.listen():
        print("There's a message")
        print(message)
        if message['type'] == 'message':
            print("The type is message")
            event_data = message['data']
            # Process the event data according to your application's needs
            print(f'Received event: {event_data}')


class TestStuff(unittest.IsolatedAsyncioTestCase):

    async def test_my_func(self):
        timeout = 6000
        task = asyncio.create_task(listen_redis())  # Start the task asynchronously

        # messages = ['message 1', 'message 2', 'message 3']
        # for message in messages:
        #     await asyncio.sleep(5)
        #     await redis_client.publish('blocks', message)

        try:
            await asyncio.wait_for(task, timeout=timeout)  # Wait for the task to complete or timeout
        except asyncio.TimeoutError:
            pass  # Handle the timeout error if needed


if __name__ == '__main__':
    unittest.main()


