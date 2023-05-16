"""
This is a simple example of usage of CallbackData factory
For more comprehensive example see callback_data_factory.py
"""
import json
import logging
import typing
# now make timer run all the time keeping track of lottery and end lottery when time is up.
# bruh I tried and now that shit run forever
# tried making backend client
# now you make it work with bot ok?

# fix the GitHub tmr

import aiohttp
import asyncio

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils.callback_data import CallbackData
from aiogram.utils.exceptions import MessageNotModified

from os import environ
from datetime import datetime
from flask import request, jsonify
import requests

from Database.database.model import Lottery
from Database.backendClient import BackendClient
from lottery_timer import LotteryTimer

logging.basicConfig(level=logging.INFO)

API_TOKEN = environ.get("BotApi")
client = BackendClient()
DATABASE_URL = client.get_base_url()
# DATABASE_URL = environ.get("DATABASE_URL")

bot = Bot(token=API_TOKEN)
timer = LotteryTimer(bot)

dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

vote_cb = CallbackData("vote", "action")  # vote:<action>

givenTime = 1  # minutes


def get_keyboard():
    keyboard = types.InlineKeyboardMarkup()

    keyboard.row(
        types.InlineKeyboardButton("🍓", callback_data=vote_cb.new(action="strawberry")),
        types.InlineKeyboardButton("🍎", callback_data=vote_cb.new(action="apple")),
    )

    keyboard.row(
        types.InlineKeyboardButton("🍐", callback_data=vote_cb.new(action="pear")),
        types.InlineKeyboardButton("🍌", callback_data=vote_cb.new(action="banana")),
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

    idLottery = await client.get_id_lottery()
    if not isinstance(idLottery, int):
        dlottery = await client.start_lottery()
        await message.reply(
            f"Lottery started! {dlottery[0]['givenTime']} minutes left! \n"
            f"You can vote a fruit!",
            reply_markup=get_keyboard(),
        )
    else:
        timeLeft = await client.time_left(idLottery)
        if timeLeft < 0:
            await client.stop_lottery()
            dlottery = await client.start_lottery()
            if dlottery:
                print(dlottery)
                return await message.reply(
                    f"Lottery started! {dlottery[0]['givenTime']} minutes left! \n"
                    f"You can vote a fruit!",
                    reply_markup=get_keyboard(),
                )
            else:
                return await message.reply(f"Error")
        else:
            await message.reply(
                f"Lottery is running! {timeLeft} minutes left! \n"
                f"You can vote a fruit!",
                reply_markup=get_keyboard(),
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
        timeLeft = await client.time_left(idLottery)
        if timeLeft < 0:
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
                f"lottery is running. {timeLeft} minutes left! \n"
                f"You can vote a fruit!",
                reply_markup=get_keyboard(),
            )


@dp.callback_query_handler(
    vote_cb.filter(action=["strawberry", "apple", "pear", "banana"])
)
async def callback_vote_action(
    query: types.CallbackQuery, callback_data: typing.Dict[str, str]
):
    logging.info(
        "Got this callback data: %r", callback_data
    )  # callback_data contains all info from callback data
    await query.answer()  # don't forget to answer callback query as soon as possible
    callback_data_action = callback_data["action"]

    idLottery = await client.get_id_lottery()
    if not isinstance(idLottery, int):
        await bot.edit_message_text(
            "No lottery is running", query.message.chat.id, query.message.message_id
        )
        return
    else:
        timeLeft = await client.time_left(idLottery)
        if timeLeft <= 0:
            winners = await client.get_winners(idLottery)
            if not winners:
                await bot.edit_message_text(
                    f"No one have won the lottery!", query.message.chat.id, query.message.message_id
                )
            else:
                await bot.edit_message_text(
                    f"Lottery have ended!\n"
                    f"Winners are {winners}" , query.message.chat.id, query.message.message_id
                )
            await client.stop_lottery()
            return
    user_name = query.from_user.username
    user_id = query.from_user.id

    emojiDict = {"🍓": "strawberry", "🍎": "apple", "🍐": "pear", "🍌": "banana"}  # might need better solution but not now
    weirdEmoji = False
    reaction = None
    if callback_data_action in emojiDict.values():
        reaction = callback_data_action

    if reaction is None:
        weirdEmoji = True

    if not weirdEmoji:
        bet = await client.post_bet(user_id, idLottery, reaction)

        if bet == {'message': 'Already voted on this lottery'}:
            await bot.edit_message_text(
                f"User {user_name} have already voted on this lottery! \n"
                f"{timeLeft} minutes left ",
                query.message.chat.id,
                query.message.message_id,
                reply_markup=get_keyboard(),
            )

        elif bet == {'message': 'Lottery not found'}:
            await bot.edit_message_text(
                f"Lottery not found!",
                query.message.chat.id,
                query.message.message_id,
                reply_markup=get_keyboard(),
            )

        else:
            await bot.edit_message_text(
                f"{user_name} voted {reaction} \n" f"{timeLeft} minutes left ",
                query.message.chat.id,
                query.message.message_id,
                reply_markup=get_keyboard(),
            )


@dp.errors_handler(
    exception=MessageNotModified
)  # handle the cases when this exception raises
async def message_not_modified_handler(update, error):
    return True  # errors_handler must return True if error was handled correctly


if __name__ == "__main__":
    print("Launching Timeout Worker")
    loop = asyncio.get_event_loop()
    asyncio.run_coroutine_threadsafe(timer.notify(), loop)
    print("Launching Bot Worker")
    executor.start_polling(dp, skip_updates=True)
    # loop.close()
    # asyncio.run(main())

