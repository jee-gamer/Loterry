import json
import logging
import time
import typing
import aiohttp
import asyncio
from contextlib import suppress

from aiogram import Bot, Dispatcher, executor, types, filters
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils.callback_data import CallbackData
from aiogram.utils.exceptions import MessageNotModified

from os import environ

from BackendClient.backendClient import BackendClient
from lottery_timer import LotteryTimer  # this run the class
from BitcoinWorker.client import BlockstreamClient
import redis.asyncio as redis
from uuid import uuid4

# from BitcoinWorker.app import REDIS_HOST, REDIS_PORT  # this run the class
# cut out the complication first, talk later

logging.basicConfig(level=logging.INFO)


API_TOKEN = environ.get("BotApi")
client = BackendClient()
# HEAVY EXPERIMENT

REDIS_HOST = environ.get("host", default="localhost")
REDIS_PORT = environ.get("port", default=6379)
redis_server = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)


DATABASE_URL = client.get_base_url()
# DATABASE_URL = environ.get("DATABASE_URL")

bot = Bot(token=API_TOKEN)
timer = LotteryTimer(bot)

dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

bet_cb = CallbackData("bet", "action", "lottery")  # vote:<action>


def get_keyboard(lottery: int):
    keyboard = types.InlineKeyboardMarkup()

    keyboard.row(
        types.InlineKeyboardButton(
            "odd", callback_data=bet_cb.new(action=f"odd", lottery=str(lottery))
        ),
        types.InlineKeyboardButton(
            "even", callback_data=bet_cb.new(action=f"even", lottery=str(lottery))
        ),
    )

    return keyboard


@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    data = None
    if message.from_user.username is None:
        username = "No Username"
    else:
        username = message.from_user.username

    user_data = {
        "id": message.from_user.id,
        "alias": username,
        "firstName": message.from_user.first_name,
        "lastName": message.from_user.last_name,
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{DATABASE_URL}/users", json=user_data) as response:
            data = await response.json()
            print(data)

    await message.reply(
        "Welcome here. This is a Lottery bot where people play against each other"
        "\n"
        "type /Lottery to start/see ongoing Lottery"
        "\n"
        "type /result to see the Lottery results"
    )


@dp.message_handler(commands=["lottery"])
async def cmd_lottery(message: types.Message):
    idLottery = await client.get_id_lottery()  # always return int if lottery is running
    if not isinstance(idLottery, int):
        await client.start_lottery()
        height = await client.get_height()
        await message.reply(
            f"Lottery started! {height} started height\n" f"You can vote odd or even!",
            reply_markup=get_keyboard(lottery=idLottery),
        )
    else:
        height = await client.get_height()
        await message.reply(
            f"Lottery is running! {height} started height\n"
            f"You can vote odd or even!",
            reply_markup=get_keyboard(lottery=idLottery),
        )


@dp.callback_query_handler(bet_cb.filter(action=["odd", "even"]))
async def callback_vote_action(
    query: types.CallbackQuery, callback_data: typing.Dict[str, str]
):
    await query.answer(
        text="Submitting bet"
    )  # don't forget to answer callback query as soon as possible
    # check redis
    if not await redis_server.ping():
        logging.error(f"No ping to Redis {REDIS_HOST}:{REDIS_PORT}")
        return

    print('still working')
    logging.debug("Redis pinged. Sending a message")

    await redis_server.publish(
        "bets",
        json.dumps(
            {
                "uuid": uuid4().hex,
                "idUser": query.from_user.id,
                "idLottery": callback_data["lottery"],
                "userBet": callback_data["action"],
            }
        ),
    )

    logging.info(
        f'Sent user {query.from_user.id} bet {callback_data["lottery"]} in Lottery {callback_data["lottery"]}'
    )

    return await query.answer(
        text="Submitted", show_alert=True
    )


@dp.errors_handler(
    exception=MessageNotModified
)  # handle the cases when this exception raises
async def message_not_modified_handler(update, error):
    return True  # errors_handler must return True if error was handled correctly


async def notify():
    logging.info("Notification task started")
    while True:
        logging.info("Notify beat")
        await asyncio.sleep(100)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    future = asyncio.run_coroutine_threadsafe(notify(), loop)

    executor.start_polling(dp, loop=loop, skip_updates=False)

    try:
        result = future.result(timeout=1.0)
    except asyncio.TimeoutError:
        print("The coroutine took too long, cancelling the task...")
        future.cancel()
    except Exception as exc:
        print(f"The coroutine raised an exception: {exc!r}")
    else:
        print(f"The coroutine returned: {result!r}")
