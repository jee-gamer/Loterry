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

from lottery import Lottery

logging.basicConfig(level=logging.DEBUG)

API_TOKEN = environ.get('BotApi')


bot = Bot(token=API_TOKEN)

dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

vote_cb = CallbackData('vote', 'action')  # vote:<action>
likes = {}  # user_id: amount_of_likes
BotLottery = Lottery()


def get_keyboard():
    keyboard = types.InlineKeyboardMarkup()

    keyboard.row(
        types.InlineKeyboardButton('🍓', callback_data=vote_cb.new(action='strawberry')),
        types.InlineKeyboardButton('🍎', callback_data=vote_cb.new(action='apple'))
                 )

    keyboard.row(
        types.InlineKeyboardButton('🍐', callback_data=vote_cb.new(action='pear')),
        types.InlineKeyboardButton('🍌', callback_data=vote_cb.new(action='banana'))
                )
    return keyboard




@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.reply(f'Welcome here. This is a Lottery bot where people play against each other'
                        f'\n'
                        f'type /startLottery to start Lottery'
                        f'\n'
                        f'type /Lottery to see ongoing Lottery')

lottery_start = 0

@dp.message_handler(commands=['startLottery'])
async def cmd_start(message: types.Message):
    global lottery_start
    if lottery_start == 0:
        global timenow
        timenow = time.time()
        amount_of_likes = likes.get(message.from_user.id, 0)  # get value if key exists else set to 0
        await message.reply(f'Loterry Started!' f'\n'
                            f'Vote! You have 4 fruits to choose from.', reply_markup=get_keyboard())
        lottery_start = 1
    else:
        await message.reply(f'Lottery was already started!')
@dp.message_handler(commands=['Lottery'])
async def cmd_start(message: types.Message):
    global lottery_start
    if lottery_start == 1:
        timenow2 = time.time()
        difference = int(timenow2) - int(timenow)
        differnece_min = difference / 60
        timeleft = 60 - differnece_min
        global timeleftround
        timeleftround = round(timeleft, 1)
        amount_of_likes = likes.get(message.from_user.id, 0)  # get value if key exists else set to 0
        await message.reply(f'Vote! You have 4 fruits to choose from.' f'\n'
                            f'{timeleftround} Minutes Left', reply_markup=get_keyboard())
    else:
        await message.reply(f'Lottery have not started!')

timeout = 0
@dp.callback_query_handler(vote_cb.filter(action=['strawberry', 'apple', 'pear', 'banana']))
async def callback_vote_action(query: types.CallbackQuery, callback_data: typing.Dict[str, str]):
    logging.info('Got this callback data: %r', callback_data)  # callback_data contains all info from callback data
    await query.answer()  # don't forget to answer callback query as soon as possible
    callback_data_action = callback_data['action']

    likes_count = likes.get(callback_data_action, 0)
    likes_count += 1



    likes[callback_data_action] = likes_count  # update amount of likes in storage

    await bot.edit_message_text(
        f'You voted {callback_data_action}! Now {callback_data_action} have {likes_count} vote[s].',
        query.from_user.id,
        query.message.message_id,
        reply_markup=get_keyboard(),
    )



@dp.errors_handler(exception=MessageNotModified)  # handle the cases when this exception raises
async def message_not_modified_handler(update, error):
    return True # errors_handler must return True if error was handled correctly


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

# while True:
#     if timeleftround == 0:
#         @dp.callback_query_handler(vote_cb.filter(action=['Strawberry', 'Apple', 'Pear', 'Banana']))
#         async def callback_vote_action(query: types.CallbackQuery, callback_data: typing.Dict[str, str]):
#             logging.info('Got this callback data: %r',
#                          callback_data)  # callback_data contains all info from callback data
#             await query.answer()  # don't forget to answer callback query as soon as possible
#             callback_data_action = callback_data['action']
#             likes_count = likes.get(callback_data_action, 0)
#             likes_count += 1
#
#             strawberry_likes_count = likes.get(callback_data['Strawberry'], 0)
#             apple_likes_count = likes.get(callback_data['Apple'], 0)
#             pear_likes_count = likes.get(callback_data['Pear'], 0)
#             banana_likes_count = likes.get(callback_data['Banana'], 0)
#
#             print(strawberry_likes_count)
#
#
#             likes[callback_data_action] = likes_count  # update amount of likes in storage
#
#             await bot.edit_message_text(
#                 f'You voted {callback_data_action}! Now {callback_data_action} have {likes_count} vote[s].',
#                 query.from_user.id,
#                 query.message.message_id,
#                 reply_markup=get_keyboard(),
#             )
