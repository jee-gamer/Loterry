import json
import logging
import typing
import aiohttp
import asyncio


from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils.callback_data import CallbackData
from aiogram.utils.exceptions import MessageNotModified

from os import environ

from backendClient import BackendClient
from lottery_timer import LotteryTimer  # this run the class
import redis.asyncio as redis
from uuid import uuid4

# from BitcoinWorker.app import REDIS_HOST, REDIS_PORT  # this run the class
# cut out the complication first, talk later

logging.basicConfig(level=logging.INFO)


API_TOKEN = environ.get("BotApi")
client = BackendClient()

REDIS_HOST = environ.get("host", default="localhost")
REDIS_PORT = environ.get("port", default=6379)
redis_service = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)
notification_sub = redis_service.pubsub()


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
        "type /result to see the Lottery results (not active)"
    )


@dp.message_handler(commands=["lottery"])
async def cmd_lottery(message: types.Message):
    BTC_URL = "http://localhost:5001"
    endpoint = "/tip"
    height = None
    # TODO: move it into make_request handler
    async with aiohttp.ClientSession() as session:
        url = f"{BTC_URL}{endpoint}"
        async with session.request("GET", url) as response:
            height = await response.json()
            if not height:
                await message.reply(f"Couldnt  start lottery! Received {height} as a height")

    idLottery = await client.get_lottery(id=height)
    # In Python we have None type
    if idLottery:
        height = await client.get_height()
        #TODO: Put deeplink onto bot here for unregistered users
        await message.reply(
            f"Lottery is running! {height} started height\n https://t.me/StreetBitTestBot"
            f"You can vote odd or even!",
            reply_markup=get_keyboard(lottery=idLottery),
        )
    else:
        await client.start_lottery()
        #TODO: Put deeplink onto bot here for unregistered users
        await message.reply(
            f"Lottery started! {height} started height\n" f"You can vote odd or even! https://t.me/StreetBitTestBot",
            reply_markup=get_keyboard(lottery=height),
        )


@dp.callback_query_handler(bet_cb.filter(action=["odd", "even"]))
async def callback_bet_action(
    query: types.CallbackQuery, callback_data: typing.Dict[str, str]
):
    await query.answer(
        text="Submitting bet"
    )  # don't forget to answer callback query as soon as possible
    # check redis
    if not await redis_service.ping():
        logging.error(f"No ping to Redis {REDIS_HOST}:{REDIS_PORT}")
        return

    logging.debug("Redis pinged. Sending a message")

    await redis_service.publish(
        "bets",
        json.dumps(
            {
                "uuid": uuid4().hex, # common thing in software development
                "idUser": query.from_user.id,
                "idLottery": callback_data["lottery"],
                "userBet": callback_data["action"],
                "betSize": 1000,
            }
        ),
    )

    logging.info(
        f'Sent user {query.from_user.id} bet {callback_data["action"]} in Lottery {callback_data["lottery"]}'
    )

    return await query.answer(
        text="Submitted", show_alert=True
    )


@dp.errors_handler(
    exception=MessageNotModified
)  # handle the cases when this exception raises
async def message_not_modified_handler(update, error):
    return True  # errors_handler must return True if error was handled correctly


async def listen():
    while True:
        message = await notification_sub.get_message(ignore_subscribe_messages=True)
        if message and "data" in message:
            logging.info(f"received: {message}")
            str_data = message["data"].decode()
            try:
                data = json.loads(str_data)
                logging.info(f"decoded JSON: {data}")
                for user in data.keys():
                    user_id = int(user)
                    logging.info(f"sending a message to {user_id}")
                    await bot.send_message(user_id, data[user])
            except Exception as e:
                logging.error(f"exception during sending message to user: {e}")
                continue
        await asyncio.sleep(0.1)


async def notify():
    async with notification_sub as pubsub:
        await pubsub.subscribe("notify")
        future = asyncio.create_task(listen())
        await redis_service.publish("notify", "Notification task started!")
        await future


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
