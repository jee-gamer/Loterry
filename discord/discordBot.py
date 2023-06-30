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
            "tg/bets",
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

    @discord.ui.button(label="odd", style=discord.ButtonStyle.red)
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
    idUser = str(message.author.id)
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
            "id": int(idUser),
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
        # In Python we have None type
        if idLottery:
            height = await client.get_height()
            msg = f"Lottery is running, {height} started height\nYou can vote odd or even\n"

        elif idLottery2:  # because we disable the voting when the height move 1st time then stop lottery the 2nd time
            height = await client.get_height()
            msg = f"Lottery voting time is up, {height} started height\nYou can vote odd or even\n "

        else:
            await client.start_lottery()
            msg = f"Lottery started, {height} started height\nYou can vote odd or even\n"

        view = VoteButton(height=height)
        replyMessage = await message.reply(msg, view=view)
        view.message = replyMessage

    elif re.match(r"!deposit\s([0-9]+)", p_message):
        logging.info("HE DEPOSITING???")
        pass
    elif re.match(r'!withdraw\s(lnbc)([0-9]+)[a-zA-Z0-9]+[0-9a-zA-Z=]+', p_message):
        logging.info("HE WITHDRAWING???")
        pass
    elif p_message == "!balance":
        logging.info("HE BALANCE???")
        pass
    elif p_message == "!help":
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


if __name__ == "__main__":
    logging.info(API_TOKEN)
    bot.run(API_TOKEN)
    logging.info("Bot Stopped")
