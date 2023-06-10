"""
This is a simple example of usage of CallbackData factory
For more comprehensive example see callback_data_factory.py

RUN DATABASE APP BEFORE RUNNING THIS!!!
"""
import json
import logging
import time
import typing

# now make actual subscriber

import aiohttp
import asyncio

from aiogram import Bot, Dispatcher, executor, types, filters
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils.callback_data import CallbackData
from aiogram.utils.exceptions import MessageNotModified

from os import environ

from BackendClient.backendClient import BackendClient
from lottery_timer import LotteryTimer  # this run the class
from BitcoinWorker.client import BlockstreamClient
import redis.asyncio as redis

# from BitcoinWorker.app import REDIS_HOST, REDIS_PORT  # this run the class
# cut out the complication first, talk later

logging.basicConfig(level=logging.INFO)


API_TOKEN = environ.get("BotApi")
client = BackendClient()
bcClient = BlockstreamClient()  # this run the class init too
# HEAVY EXPERIMENT
redis_server = redis.Redis(host="localhost", port=6379, db=0)


DATABASE_URL = client.get_base_url()
# DATABASE_URL = environ.get("DATABASE_URL")

bot = Bot(token=API_TOKEN)
timer = LotteryTimer(bot)

dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

vote_cb = CallbackData("vote", "action", "lottery")  # vote:<action>

givenTime = 1  # minutes


async def post_winning():
    currentHash = await bcClient.get_current_hash()
    decimalId = int(currentHash, 16)
    if decimalId % 2 == 0:
        print('even')
        await client.post_winning_choice('even')
    else:
        print('odd')
        await client.post_winning_choice('odd')


def get_keyboard(lottery: int):
    keyboard = types.InlineKeyboardMarkup()

    keyboard.row(
        types.InlineKeyboardButton("odd", callback_data=vote_cb.new(action=f"odd", lottery=str(lottery))),
        types.InlineKeyboardButton("even", callback_data=vote_cb.new(action=f"even", lottery=str(lottery))),
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
        "type /startLottery to start Lottery"
        "\n"
        "type /Lottery to see ongoing Lottery"
        "\n"
        "type /result to see the Lottery results"
    )


@dp.message_handler(commands=["startLottery", "startlottery"])
async def cmd_start(message: types.Message):

    idLottery = await client.get_id_lottery()  # always return int if lottery is running
    if not isinstance(idLottery, int):
        await client.start_lottery()
        height = await client.get_height()
        await message.reply(
            f"Lottery started! {height} started height\n"
            f"You can vote odd or even!",
            reply_markup=get_keyboard(lottery=idLottery),
        )
    else:
        height = await client.get_height()
        await message.reply(
            f"Lottery is running! {height} started height\n"
            f"You can vote odd or even!",
            reply_markup=get_keyboard(lottery=idLottery),
        )


@dp.message_handler(
    commands=["Lottery", "lottery", "result"]
)  # lottery = 2 is when we got the result
async def cmd_start(message: types.Message):
    idLottery = await client.get_id_lottery()

    if not isinstance(idLottery, int):
        await message.reply(
            "lottery isn't running! Start Lottery by typing /startLottery"
        )
    else:
        height = await client.get_height()
        lastHeight = await bcClient.get_last_height()
        if lastHeight > height+1:
            await post_winning()
            await client.stop_lottery()
            winners = await client.get_winners(idLottery)
            if not winners:
                await message.reply(
                    f"Time is up and No one have won the lottery!"
                )
            else:
                await message.reply(
                    f"Lottery have ended!\n"
                    f"Winners are {winners}"
                )
            await client.stop_lottery()

        else:
            await message.reply(
                f"lottery is running. {height} started height \n"
                f"You can vote odd or even!",
                reply_markup=get_keyboard(lottery=idLottery),
            )


@dp.callback_query_handler(
    vote_cb.filter(action=['odd', 'even'])
)
async def callback_vote_action(
    query: types.CallbackQuery, callback_data: typing.Dict[str, str]
):
    logging.info(
        "Got this callback data: %r", callback_data
    )  # callback_data contains all info from callback data

    await query.answer(text="Submitting bet")  # don't forget to answer callback query as soon as possible
    callback_data_action = callback_data["action"]
    idLottery = callback_data["lottery"]  # what's this?

    # check redis
    if not await redis_server.ping():
        raise ConnectionError("No connection with redis")
    else:
        print("Redis pinged. Started syncing")

    user_id = query.from_user.id

    bet = {
        "idUser": user_id,
        "idLottery": idLottery,
        "userBet": callback_data_action
    }

    await redis_server.publish('bets', json.dumps(bet))
    await query.answer(text="Submitted")
    print('sent bet')

    #
    # # bet = await client.post_bet(user_id, idLottery, reaction)
    #
    # if bet == {'message': 'Already voted on this lottery'}:
    #     await bot.edit_message_text(
    #         f"User {user_name} have already voted on this lottery! \n"
    #         f"{height} height started",
    #         query.message.chat.id,
    #         query.message.message_id,
    #         reply_markup=get_keyboard(),
    #     )
    #
    # elif bet == {'message': 'Lottery not found'}:
    #     await bot.edit_message_text(
    #         f"Lottery not found!",
    #         query.message.chat.id,
    #         query.message.message_id,
    #         reply_markup=get_keyboard(),
    #     )
    #
    # else:
    #     await bot.edit_message_text(
    #         f"{user_name} voted {reaction} \n" f"{height} height started ",
    #         query.message.chat.id,
    #         query.message.message_id,
    #         reply_markup=get_keyboard(),
    #     )


@dp.errors_handler(
    exception=MessageNotModified
)  # handle the cases when this exception raises
async def message_not_modified_handler(update, error):
    return True  # errors_handler must return True if error was handled correctly


if __name__ == "__main__":
    print("Launching Timeout Worker")
    # loop = asyncio.get_event_loop()
    # asyncio.run_coroutine_threadsafe(timer.notify(), loop)
    print("Launching Bot Worker")
    executor.start_polling(dp, skip_updates=True)
    # loop.close()
    # asyncio.run(main())
