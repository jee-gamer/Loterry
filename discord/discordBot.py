import json
import logging
import re
import typing
import aiohttp
import asyncio
import discord
from discord import ButtonStyle
from discord.ext import commands

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher.filters import RegexpCommandsFilter
from aiogram.utils.callback_data import CallbackData
from aiogram.utils.exceptions import MessageNotModified
from aiogram.contrib.fsm_storage.redis import RedisStorage2

from os import environ
from typing import Union
from backendClient import BackendClient
import redis.asyncio as redis
from uuid import uuid4

# these are just for local testing
# from dotenv import load_dotenv
# load_dotenv()

logging.basicConfig(level=logging.INFO)

REDIS_HOST = environ.get("REDIS_HOST", default="localhost")
REDIS_PORT = environ.get("REDIS_PORT", default=6379)
DB_HOST = environ.get("DB_HOST", default="localhost")
DB_PORT = environ.get("DB_PORT", default=5000)
DATABASE_URL = f"http://{DB_HOST}:{DB_PORT}/api"
BTC_HOST = environ.get("BTC_HOST", default="localhost")
BTC_PORT = environ.get("BTC_PORT", default=5001)
BTC_URL = f"http://{BTC_HOST}:{BTC_PORT}"
LNBITS_API = environ.get("LNBITS_API")


redis_service = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)
notification_sub = redis_service.pubsub()

storage = RedisStorage2(host=REDIS_HOST, port=REDIS_PORT, db=5)

API_TOKEN = environ.get("DiscordBotApi")
client = BackendClient()

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)


@bot.event
async def on_ready():
    print(f"{bot.user} is now running")
    print("Logged in as")
    print(bot.user.name)
    print(bot.user.id)
    print("------")


class VoteButton(discord.ui.View):  # button class
    def __init__(self, height):
        super().__init__()
        self.height = height

    async def disable_all_items(self):
        for item in self.children:
            item.disabled = True
        await self.message.edit(view=self)

    async def send_redis(self, idUser, lottery, action):
        logging.debug("Redis pinged. Sending a message")

        await redis_service.publish(
            "discord/bets",
            json.dumps(
                {
                    "uuid": uuid4().hex,  # common thing in software development
                    "idUser": idUser,
                    "idLottery": lottery,
                    "userBet": action,
                    "betSize": 1000
                }
            ),
        )

        logging.info(
            f'Sent user {idUser} bet in Lottery {lottery} ,{action}'
        )

    @discord.ui.button(label="odd", style=discord.ButtonStyle.red)  # BUTTON IS BROKEN
    async def odd(self, interaction: discord.Interaction, button: discord.ui.Button):
        # await interaction.response.send_message("working")         --THIS IS HOW YOU RESPOND TO INTERACTION
        idUser = interaction.user.id
        if not await redis_service.ping():
            logging.error(f"No ping to Redis {REDIS_HOST}:{REDIS_PORT}")
            return
        await self.send_redis(idUser, self.height, "odd")

    @discord.ui.button(label="even", style=discord.ButtonStyle.blurple)
    async def even(self, interaction: discord.Interaction, button: discord.ui.Button):
        idUser = interaction.user.id
        if not await redis_service.ping():
            logging.error(f"No ping to Redis {REDIS_HOST}:{REDIS_PORT}")
            return
        await self.send_redis(idUser, self.height, "even")


@bot.event
async def on_message(message):
    if not message.content.startswith("!"):
        return

    if message.author == bot.user:
        return

    # just as guide
    username = str(message.author)
    idUser = int(message.author.id)
    userMessage = str(message.content)
    channel = str(message.channel)
    logging.info(f"{username} id:{idUser} said {userMessage} in {channel}")

    private = False  # private chat or not?

    if userMessage[0] == "?":
        private = True
        userMessage = userMessage[1:]

    # start to check message
    p_message = str(message.content).lower()
    if p_message == "!start":
        data = None
        user_data = {
            "id": idUser,
            "alias": username,
            "firstName": "discord",
            "lastName": "discord"
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{DATABASE_URL}/users", json=user_data) as response:
                data = await response.json()
                logging.info(data)

        await message.reply(
            "Welcome here. This is a Lottery bot where people play against each other"
            "\n"
            "type !Lottery to start/see ongoing Lottery"
            "\n"
            "type !deposit #amount to deposit money"
            "\n"
            "type !withdraw #invoiceId to withdraw money"
            "\n"
            "type !balance to check your balance in the bot"
        )
    elif p_message == "!lottery":

        endpoint = "/tip"
        #registerDeepLink = "[here](https://t.me/Hahafunnybot?start=default)"

        height = None
        async with aiohttp.ClientSession() as session:
            url = f"{BTC_URL}{endpoint}"
            logging.info(url)
            async with session.request("GET", url) as response:
                height = await response.json()
                if not height:
                    await message.reply(f"Couldn't  start lottery! Received {height} as a height")
                    return

        idLottery = await client.get_lottery(id=height)
        idLottery2 = await client.get_lottery(id=height - 1)
        idLottery3 = await client.get_lottery(id=height - 2)
        # In Python we have None type

        if idLottery:
            height = await client.get_height()
            msg = f"Lottery is running, {height} started height\nYou can vote odd or even\n"
            view = VoteButton(height=height)
            replyMessage = await message.reply(msg, view=view)
            view.message = replyMessage
            return
        elif idLottery2:  # because we disable the voting when the height move 1st time then stop lottery the 2nd time
            height = await client.get_height()
            msg = f"Lottery voting time is up, {height} started height\nYou can vote odd or even\n "
        elif idLottery3:  # cooldown to announce results
            height = await client.get_height()
            msg = f"Lottery is on cooldown!, {height} started height\nYou can start new lottery when next block comes"
        else:
            await client.start_lottery()
            msg = f"Lottery started, {height} started height\nYou can vote odd or even\n"

        replyMessage = await message.reply(msg)

    elif re.match(r"!deposit\s([0-9]+)", p_message):
        logging.info("HE DEPOSITING???")
        inputs = p_message.split(" ")
        try:
            amount = int(inputs[1])
        except ValueError:
            return await message.reply(
                "Incorrect number provided"
            )

        async with aiohttp.ClientSession() as session:
            header = {"X-Api-Key": LNBITS_API}
            data = {"out": False, "amount": amount, "memo": f"{idUser}", "expiry": 7200}  # 2 hour
            async with session.post(f"https://legend.lnbits.com/api/v1/payments",
                                    headers=header,
                                    json=data) as response:
                data = await response.json()
                try:
                    paymentRequest = data['payment_request']
                    invoiceInfo = {"idUser": idUser,
                                   "paymentHash": data['payment_hash']
                                   }

                    await redis_service.publish('discord/invoice', json.dumps(invoiceInfo))
                except Exception as e:
                    logging.info(e)
                return await message.reply(
                    f"{paymentRequest}"
                )

    elif re.match(r'!withdraw\s(lnbc)([0-9]+)[a-zA-Z0-9]+[0-9a-zA-Z=]+', p_message):
        logging.info("HE WITHDRAWING???")
        inputs = p_message.split(" ")

        pattern = r"^(lnbc)([0-9]+)[a-zA-Z0-9]+[0-9a-zA-Z=]+"
        bolt11 = re.match(pattern, inputs[1])
        if not bolt11:
            logging.info("bolt11 value is incorrect")
            return await message.reply(
                "Incorrect invoiceId provided!"
            )
        else:
            bolt11 = re.search(r"^(lnbc)([0-9]+)[a-zA-Z0-9]+[0-9a-zA-Z=]+", inputs[1])
            amount = int(bolt11.group(2)) / 10
            invoiceInfo = {"idUser": idUser,
                           "bolt11": inputs[1],
                           "amount": amount  # BROKEN BROKEN
                           }
            logging.info(f"sending invoice info {invoiceInfo}")
            await redis_service.publish('discord/withdraw', json.dumps(invoiceInfo))

    elif p_message == "!balance":
        logging.info("HE BALANCE???")
        async with aiohttp.ClientSession() as session:
            url = f"http://{DB_HOST}:{DB_PORT}/api/users/balance?id={idUser}"
            async with session.request("GET", url) as response:
                balance = -1
                balance = await response.json()
                logging.info(balance)
                if balance == {'message': 'User not found'} or balance == -1:
                    await message.reply(f"User is not registered \nregister by typing !start")

                else:
                    await message.reply(f"You have {balance} balance")


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
                    user = await bot.fetch_user(user_id)
                    msg = data[user]
                    await user.send(msg)
            except Exception as e:
                logging.error(f"exception during sending message {message} to user: {e}")
                continue
        await asyncio.sleep(0.1)


async def notify():
    async with notification_sub as pubsub:
        await pubsub.subscribe("discord/notify")
        future = asyncio.create_task(listen())
        await redis_service.publish("discord/notify", "Notification task started!")
        await future


if __name__ == "__main__":
    logging.info(API_TOKEN)
    loop = asyncio.get_event_loop()
    future = asyncio.run_coroutine_threadsafe(notify(), loop)
    bot.run(API_TOKEN)
    try:
        result = future.result(timeout=1.0)
    except asyncio.TimeoutError:
        print("The coroutine took too long, cancelling the task...")
        future.cancel()
    except Exception as exc:
        print(f"The coroutine raised an exception: {exc!r}")
    else:
        print(f"The coroutine returned: {result!r}")
    logging.info("Bot Stopped")
