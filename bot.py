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

l = None
lotteryStart = 0
givenTime = 30  # seconds


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
    global lotteryStart
    global l

    if lotteryStart == 0 or lotteryStart == 2:

        l = Lottery(time_delta=givenTime)

        timeLeft = l.time_left()
        maxVotes = l.get_max_vote()

        await message.reply(
            f"Lottery Started!"
            f"\n"
            f"Vote! You have 4 fruits to choose from. You can choose up to {maxVotes} fruits"
            f"\n"
            f"{timeLeft} minutes left!",
            reply_markup=get_keyboard(),
        )
        lotteryStart = 1

    elif lotteryStart == 1:
        timeLeft = l.time_left()
        maxVotes = l.get_max_vote()
        await message.reply(
            f"Vote! You have 4 fruits to choose from. You can choose up to {maxVotes} fruits"
            f"\n"
            f"{timeLeft} Seconds left",
            reply_markup=get_keyboard(),
        )


@dp.message_handler(commands=["Lottery", "lottery"])  # lottery = 2 is when we got the result
async def cmd_start(message: types.Message):
    maxVotes = l.get_max_vote()
    if lotteryStart == 1:
        timeLeft = l.time_left()
        await message.reply(
            f"Vote! You have 4 fruits to choose from. You can choose up to {maxVotes} fruits"
            f"\n"
            f"{timeLeft} Seconds left",
            reply_markup=get_keyboard(),
        )
    else:
        await message.reply("Lottery have not started!")


@dp.message_handler(commands=["result"])
async def cmd_start(message: types.Message):
    global lotteryStart
    username = message.from_user.username
    if username is None:
        username = f"{message.from_user.first_name} {message.from_user.last_name}"

    if lotteryStart == 1:
        if l.end_lottery():
            print(l.finish())
            lotteryStart = 2

            player, win = l.check_winner(username)

            if win == 1:
                await message.reply(f"User {player} had won the Lottery!")
            else:
                await message.reply(f"User {player} had lost the Lottery!")

        else:
            timeLeft = l.time_left()
            await message.reply(f"Lottery is ongoing! {timeLeft} seconds left!")

    elif lotteryStart == 2:
        l.finish()

        player, win = l.check_winner(username)

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

    voteCount = 0

    userVote = l.get_user_vote(user_id)

    voteCount = len(userVote)

    sameFruitVote = userVote.get(callback_data_action, 0)

    if lotteryStart == 1:
        timeLeft = l.time_left()
        maxVotes = l.get_max_vote()
        if sameFruitVote == 1:

            await bot.edit_message_text(
                f"You have already voted this fruit! \n"
                f"{timeLeft} Seconds left ",
                query.message.chat.id,
                query.message.message_id,
                reply_markup=get_keyboard(),
            )
        elif voteCount < maxVotes and sameFruitVote == 0:
            l.store_vote(callback_data_action, user_id)
            print(f"voted {callback_data_action}")

            likes_count = l.get_score(callback_data_action)

            await bot.edit_message_text(
                f"You voted {callback_data_action}! Now {callback_data_action} have {likes_count} vote[s]. \n"
                f"{timeLeft} Seconds left ",
                query.message.chat.id,
                query.message.message_id,
                reply_markup=get_keyboard(),
            )

        else:
            await bot.edit_message_text(
                f"You have already voted {maxVotes} fruit! \n" f"{timeLeft} Seconds left ",
                query.message.chat.id,
                query.message.message_id,
                reply_markup=get_keyboard(),
            )

    else:
        await bot.edit_message_text(
            "The lottery have not started!", query.message.chat.id, query.message.message_id
        )


@dp.errors_handler(
    exception=MessageNotModified
)  # handle the cases when this exception raises
async def message_not_modified_handler(update, error):
    return True  # errors_handler must return True if error was handled correctly


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
