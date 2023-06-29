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

logging.basicConfig(level=logging.INFO)

REDIS_HOST = environ.get("REDIS_HOST", default="localhost")
REDIS_PORT = environ.get("REDIS_PORT", default=6379)
DB_HOST = environ.get("DB_HOST", default="localhost")
DB_PORT = environ.get("DB_PORT", default=5000)
DATABASE_URL = f"http://{DB_HOST}:{DB_PORT}/api"
BTC_HOST = environ.get("BTC_HOST", default="localhost")
BTC_PORT = environ.get("BTC_PORT", default=5001)
BTC_URL = f"http://{BTC_HOST}:{BTC_PORT}"

API_TOKEN = environ.get("BotApi")

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
    async def disable_all_items(self):
        for item in self.children:
            item.disabled = True
        await self.message.edit(view=self)

    @discord.ui.button(label="odd", style=discord.ButtonStyle.red)
    async def odd(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("World")

    @discord.ui.button(label="even", style=discord.ButtonStyle.blurple)
    async def even(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("World")


@bot.event
async def on_message(message):
    if not message.content.startswith("!"):
        return

    if message.author == bot.user:
        return

    # just as guide
    username = str(message.author)
    userId = str(message.author.id)
    userMessage = str(message.content)
    channel = str(message.channel)
    print(f"{username} id:{userId} said {userMessage} in {channel}")

    private = False  # private chat or not?

    if userMessage[0] == "?":
        private = True
        userMessage = userMessage[1:]

    # start to check message
    p_message = str(message.content).lower()
    if p_message == "!start":
        data = None
        user_data = {
            "id": message.author.id,
            "alias": message.author,
            "firstName": "discord",
            "lastName": "discord"
        }
        # async with aiohttp.ClientSession() as session:
        #     async with session.post(f"{DATABASE_URL}/users", json=user_data) as response:
        #         data = await response.json()
        #         print(data)

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
        view = VoteButton()
        replyMessage = await message.reply("temp", view=view)
        view.message = replyMessage

    elif p_message == RegexpCommandsFilter(regexp_commands=['deposit\s([0-9]+)']):
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
    print(API_TOKEN)
    bot.run(API_TOKEN)
    print("Bot Stopped")
