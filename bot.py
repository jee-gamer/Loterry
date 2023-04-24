"""
This is a simple example of usage of CallbackData factory
For more comprehensive example see callback_data_factory.py
"""
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
from datetime import datetime
from lottery import Lottery

logging.basicConfig(level=logging.INFO)

API_TOKEN = environ.get("BotApi")
# DATABASE_URL = environ.get("DATABASE_URL")
DATABASE_URL = "http://localhost:5000"

bot = Bot(token=API_TOKEN)

dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

vote_cb = CallbackData("vote", "action")  # vote:<action>

givenTime = 10  # minutes
lottery = Lottery(time_delta=givenTime)


async def time_left():
    DATABASE_URL2 = DATABASE_URL + "/api/lottery"
    async with aiohttp.ClientSession() as session:
        async with session.get(DATABASE_URL2) as response:
            if response.status != 200:
                logging.error(f"Got {response.status} from the database")
                msg = "Something wrong in the backend. Please try later"
                logging.info(msg)
                return
            data = await response.json()
            timeLeftUnix = data[0]["createdAt"]
            now_datetime = datetime.strptime(timeLeftUnix, '%a, %d %b %Y %H:%M:%S %Z')
            timeLeft = int(datetime.now().timestamp()) - int(now_datetime.timestamp())
            timeLeft = (timeLeft/60)
            print(timeLeft)

    return timeLeft


async def winning_fruit():
    DATABASE_URL2 = DATABASE_URL + "/api/lottery/winning_fruit"
    async with aiohttp.ClientSession() as session:
        async with session.get(DATABASE_URL2) as response:
            if response.status != 200:
                logging.error(f"Got {response.status} from the database")
                msg = "Something wrong in the backend. Please try later"
                logging.info(msg)
                return
            data = await response.json()
            print(data)

    return data


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


"""
        lotteryStart = 0 :  the lottery have not started
        lotteryStart = 1 :  the lottery is ongoing
        lotteryStart = 2 :  the lottery ended and we have to result
"""


@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    DATABASE_URL2 = DATABASE_URL+"/api/users"
    data = None
    user_data = {
        "id": message.from_user.id,
        "alias": message.from_user.username,
        "firstName": message.from_user.first_name,
        "lastName": message.from_user.last_name,
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(DATABASE_URL2, json=user_data) as response:
            if response.status != 200:
                logging.error(f"Got {response.status} from the database")
                msg = "Something wrong in the backend. Please try later"
                return await message.reply(msg)
            data = await response.json()

    logging.info(data)
    if not data or ("status" in data.keys() and data["status"] == "error"):
        logging.error(f"Received {data} from the database")
        msg = "Something wrong in the backend. Please try later"
        return await message.reply(msg)

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

    maxVote = lottery.get_max_vote()
    await winning_fruit()
    timeLeft = await time_left()

    if timeLeft == 0:
        lottery.start()
        await message.reply(
            f"Lottery started! {givenTime} minutes left! \n"
            f"You can vote up to {maxVote} fruit",
            reply_markup=get_keyboard(),
        )
    elif timeLeft < 0:
        winners = lottery.get_winner()
        print(winners)
        winners_str = ", ".join(winners)

        if winners:
            lottery.reset()
            lottery.start()
            await message.reply(
                f"The last lottery winners are {winners_str} \n"
                f"Lottery started! {givenTime} minutes left!",
                reply_markup=get_keyboard(),
            )

        else:
            lottery.reset()
            lottery.start()
            await message.reply(
                f"No one had won the last lottery!\n"
                f"Lottery started! {givenTime} minutes left!",
                reply_markup=get_keyboard(),
            )

    else:
        await message.reply(
            f"Lottery is running! {timeLeft} minutes left! \n"
            f"You can vote up to {maxVote} fruit",
            reply_markup=get_keyboard(),
        )


@dp.message_handler(
    commands=["Lottery", "lottery"]
)  # lottery = 2 is when we got the result
async def cmd_start(message: types.Message):
    timeLeft = lottery.time_left()
    maxVote = lottery.get_max_vote()
    if timeLeft > 0:
        await message.reply(
            f"lottery is running. {timeLeft} minutes left! \n"
            f"You can vote up to {maxVote} fruit",
            reply_markup=get_keyboard(),
        )
    elif timeLeft == 0:
        await message.reply(
            "lottery isn't running! Start Lottery by typing !startLottery"
        )
    else:
        winners = lottery.get_winner()
        winners_str = ", ".join(winners)
        if winners:
            await message.reply(
                f"lottery is expired! User {winners_str} had won the Lottery!"
            )
        else:
            await message.reply("lottery is expired! No one had won the Lottery!")


@dp.message_handler(commands=["result"])
async def cmd_start(message: types.Message):
    timeLeft = lottery.time_left()
    maxVote = lottery.get_max_vote()
    if timeLeft < 0:
        winners = lottery.get_winner()
        winners_str = ", ".join(winners)
        print(f" winner is {winners}")
        if winners:
            await message.reply(f"User {winners_str} had won the Lottery!")
        else:
            await message.reply("No one had won the Lottery!")
    elif timeLeft == 0:
        await message.reply(
            "lottery isn't running! Start Lottery by typing !startLottery"
        )
    else:
        await message.reply(
            f"lottery is running! {timeLeft} minutes left! \n"
            f"You can vote up to {maxVote} fruit",
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
    timeLeft = lottery.time_left()

    user_id = query.from_user.username
    voteCount = 0
    userVote = lottery.get_user_vote(user_id)
    voteCount = len(userVote)
    sameFruitVote = userVote.get(callback_data_action, 0)

    if timeLeft <= 0:
        await bot.edit_message_text(
            "The time is up!", query.message.chat.id, query.message.message_id
        )
        return

    emojiDict = lottery.get_emoji_dict()
    weirdEmoji = False
    reaction = None
    if callback_data_action in emojiDict.values():
        reaction = callback_data_action

    if reaction is None:
        weirdEmoji = True

    if not weirdEmoji:
        userVote = lottery.get_user_vote(user_id)
        vote_count = len(userVote)
        sameFruitVote = userVote.get(reaction, 0)

        maxVotes = lottery.get_max_vote()

        if sameFruitVote == 1:
            print(user_id)
            await bot.edit_message_text(
                f"User {user_id} have already voted this fruit! \n"
                f"{timeLeft} minutes left ",
                query.message.chat.id,
                query.message.message_id,
                reply_markup=get_keyboard(),
            )

        elif vote_count < maxVotes and sameFruitVote == 0:
            await bot.edit_message_text(
                f"{user_id} voted {reaction} \n" f"{timeLeft} minutes left ",
                query.message.chat.id,
                query.message.message_id,
                reply_markup=get_keyboard(),
            )
            lottery.store_vote(reaction, user_id)

        else:
            await bot.edit_message_text(
                f"User {user_id} already voted 3 fruit! \n" f"{timeLeft} minutes left ",
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
    executor.start_polling(dp, skip_updates=True)
