"""
This is a simple example of usage of CallbackData factory
For more comprehensive example see callback_data_factory.py
"""

import logging
import typing

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils.callback_data import CallbackData
from aiogram.utils.exceptions import MessageNotModified

from os import environ
import time
import threading
import random

from lottery import Lottery

logging.basicConfig(level=logging.INFO)

API_TOKEN = environ.get("BotApi")


bot = Bot(token=API_TOKEN)

dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

vote_cb = CallbackData("vote", "action")  # vote:<action>

l = Lottery()
lotteryStart = 0
timeGiven = 0.4
timeNow = 0


def calculate_time():
    timeNow2 = time.time()
    difference = int(timeNow2) - int(timeNow)
    differenceMin = difference / 60
    timeLeft = timeGiven - differenceMin
    timeLeftRound = round(timeLeft, 1)
    return timeLeftRound


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


def round_over():
    global lotteryStart
    while True:
        time.sleep(1)
        if calculate_time() <= 0:
            lotteryStart = 2


t1 = threading.Thread(target=round_over)


@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    await message.reply(
        "Welcome here. This is a Lottery bot where people play against each other"
        "\n"
        "type /startLottery to start Lottery"
        "\n"
        "type /Lottery to see ongoing Lottery"
        "\n"
        "type /result to see the Lottery results"
    )


randomFruit = ""


@dp.message_handler(commands=["startLottery"])
async def cmd_start(message: types.Message):
    global lotteryStart

    if lotteryStart == 0 or lotteryStart == 2:

        t1.start()

        global timeNow
        timeNow = time.time()
        l.reset()
        await message.reply(
            f"Lottery Started!"
            f"\n"
            f"Vote! You have 4 fruits to choose from. You can choose up to 3 fruits"
            f"\n"
            f"{timeGiven} minutes left!",
            reply_markup=get_keyboard(),
        )
        lotteryStart = 1

        global randomFruit
        fruitList = ["strawberry", "pear", "apple", "banana"]
        randomFruit = random.choice(fruitList)
        print(randomFruit)

    elif lotteryStart == 1:
        timeLeftRound = calculate_time()
        await message.reply(
            f"Vote! You have 4 fruits to choose from. You can choose up to 3 fruits"
            f"\n"
            f"{timeLeftRound} Minutes Left",
            reply_markup=get_keyboard(),
        )


@dp.message_handler(commands=["Lottery"])  # lottery = 2 is when we got the result
async def cmd_start(message: types.Message):
    if lotteryStart == 1:
        timeLeftRound = calculate_time()
        await message.reply(
            f"Vote! You have 4 fruits to choose from. You can choose up to 3 fruits"
            f"\n"
            f"{timeLeftRound} Minutes Left",
            reply_markup=get_keyboard(),
        )
    else:
        await message.reply("Lottery have not started!")


@dp.message_handler(commands=["result"])
async def cmd_start(message: types.Message):
    global lotteryStart
    if lotteryStart == 1:
        await message.reply("Lottery is ongoing!")
    elif lotteryStart == 2:
        player, win = l.check_winner(randomFruit, message.from_user.username)
        if win == 1:
            await message.reply(f"User {player} had won the Lottery!")
        else:
            await message.reply(f"User {player} had lost the Lottery!")

    else:
        await message.reply("The lottery have not started!")


timeout = 0


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
    user_id = query.from_user.username
    calculate_time()
    vote_count = 0

    user_vote = l.get_user_vote(user_id)

    vote_count = len(user_vote)

    sameFruitVote = user_vote.get(callback_data_action, 0)

    if lotteryStart == 1:
        timeLeftRound = calculate_time()
        if sameFruitVote == 1:

            await bot.edit_message_text(
                f"You have already voted this fruit! \n"
                f"{timeLeftRound} Minutes Left ",
                query.message.chat.id,
                query.message.message_id,
                reply_markup=get_keyboard(),
            )
        elif vote_count <= 2 and sameFruitVote == 0:
            l.store_vote(callback_data_action, user_id)
            print(f"voted {callback_data_action}")

            likes_count = l.get_score(callback_data_action)

            await bot.edit_message_text(
                f"You voted {callback_data_action}! Now {callback_data_action} have {likes_count} vote[s]. \n"
                f"{timeLeftRound} Minutes Left ",
                query.message.chat.id,
                query.message.message_id,
                reply_markup=get_keyboard(),
            )

        else:
            await bot.edit_message_text(
                f"You have already voted 3 fruit! \n" f"{timeLeftRound} Minutes Left ",
                query.message.chat.id,
                query.message.message_id,
                reply_markup=get_keyboard(),
            )

    else:
        await bot.edit_message_text(
            "The lottery have ended!", query.message.chat.id, query.message.message_id
        )


@dp.errors_handler(
    exception=MessageNotModified
)  # handle the cases when this exception raises
async def message_not_modified_handler(update, error):
    return True  # errors_handler must return True if error was handled correctly


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
