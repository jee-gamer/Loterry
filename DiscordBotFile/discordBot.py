import discord
from discord.ext import commands
from os import environ
import random
from lottery import Lottery

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

def handle_response(message) -> str:
    p_message = message.lower()

    if p_message == 'hello':
        return 'Hey there!'

    if p_message == 'roll':
        return str(random.choice)

    if p_message == '!help':
        reply = "Welcome here. This is a Lottery bot where people play against each other"\
                "\n"\
                "type !startLottery to start Lottery"\
                "\n"\
                "type !Lottery to see ongoing Lottery"\
                "\n"\
                "type !result to see the Lottery results"

        return reply
    else:
        return 'what the hell u saying'

async def send_message(message, user_message, is_private):
    print(user_message)
    try:
        response = handle_response(user_message)
        await message.author.send(response) if is_private else await message.channel.send(response)
    except Exception as e:
        print(e)

def run_discord_bot():
    API_TOKEN = environ.get('BotApi')

    @bot.event
    async def on_ready():
        print(f'{bot.user} is now running')
        print('Logged in as')
        print(bot.user.name)
        print(bot.user.id)
        print('------')

    @bot.event
    async def on_message(message):
        if message.author == bot.user:
            return

        username = str(message.author)
        userMessage = str(message.content)
        channel = str(message.channel)
        print(f'{username} said {userMessage} in {channel}')

        if userMessage[0] == '?':
            userMessage = userMessage[1:]
            await send_message(message, userMessage, is_private=True)
        else:
            await send_message(message, userMessage, is_private=False)

    print(API_TOKEN)
    bot.run(API_TOKEN)

if __name__ == '__main__':
    run_discord_bot()
    print('Bot Stopped')