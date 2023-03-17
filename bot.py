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

logging.basicConfig(level=logging.INFO)

API_TOKEN = environ.get('BotApi')


bot = Bot(token=API_TOKEN)

dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

vote_cb = CallbackData('vote', 'action')  # vote:<action>
likes = {}  # user_id: amount_of_likes


def get_keyboard():
    keyboard = types.InlineKeyboardMarkup()
    keyboard.row(
        types.InlineKeyboardButton('Strawbery',
                                   callback_data=vote_cb.new(
                                       action='strawbery')),
        types.InlineKeyboardButton('Apple',
                                   callback_data=vote_cb.new(action='apple'))
    )
    keyboard.row(
        types.InlineKeyboardButton('Pear',
                                   callback_data=vote_cb.new(action='pear')),
        types.InlineKeyboardButton('Banana',
                                   callback_data=vote_cb.new(action='banana')))
    return keyboard


@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.reply(f'Welcome here. This is a Lottery bot where people play against each other')


@dp.message_handler(commands=['run'])
async def cmd_start(message: types.Message):
    amount_of_likes = likes.get(message.from_user.id, 0)  # get value if key exists else set to 0
    await message.reply(f'Vote! You have {amount_of_likes} votes now.', reply_markup=get_keyboard())


@dp.callback_query_handler(vote_cb.filter(action=['strawbery', 'apple', 'pear', 'banana']))
async def callback_vote_action(query: types.CallbackQuery, callback_data: typing.Dict[str, str]):
    logging.info('Got this callback data: %r', callback_data)  # callback_data contains all info from callback data
    await query.answer()  # don't forget to answer callback query as soon as possible
    callback_data_action = callback_data['action']

    likes_count = likes.get(callback_data_action, 0)
    likes_count += 1

    likes[callback_data_action] = likes_count  # update amount of likes in storage

    await bot.edit_message_text(
        f'You voted {callback_data_action}! Now you have {likes_count} vote[s].',
        query.from_user.id,
        query.message.message_id,
        reply_markup=get_keyboard(),
    )


@dp.errors_handler(exception=MessageNotModified)  # handle the cases when this exception raises
async def message_not_modified_handler(update, error):
    return True # errors_handler must return True if error was handled correctly


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
