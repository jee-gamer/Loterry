from typing import Union

import discord
from os import environ
from lottery import Lottery
import time
import threading
import random
import asyncio

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

l = Lottery()
lotteryStart = 0
timeGiven = 0.4
timeNow = 0


def round_over():
    global lotteryStart
    while True:
        time.sleep(1)
        if calculate_time() <= 0:
            lotteryStart = 2


def calculate_time():
    timeNow2 = time.time()
    difference = int(timeNow2) - int(timeNow)
    differenceMin = difference / 60
    timeLeft = timeGiven - differenceMin
    timeLeftRound = round(timeLeft, 1)
    return timeLeftRound


def round_over():
    global lotteryStart
    while True:
        time.sleep(1)
        if calculate_time() <= 0:
            lotteryStart = 2


t1 = threading.Thread(target=round_over)
randomFruit = ""

t2 = threading.Thread(target=round_over)

def handle_response(message) -> Union[tuple[str, int], str]:
    p_message = message.lower()
    print(f'He said {p_message}')

    # the value after reply is the emoji status
    if p_message == '!startlottery':

        global lotteryStart
        if lotteryStart == 0 or lotteryStart == 2:

            t1.start()

            global timeNow
            timeNow = time.time()
            lotteryStart = 1

            global randomFruit
            fruitList = ["strawberry", "pear", "apple", "banana"]
            randomFruit = random.choice(fruitList)
            print(randomFruit)

            timeLeft = calculate_time()

            return f'Startt! {timeLeft} minutes left!', 1

        elif lotteryStart == 1:
            timeLeft = calculate_time()
            return f'is it running??? {timeLeft} minutes left!', 1

    elif p_message == '!lottery':
        if lotteryStart == 1:
            timeLeft = calculate_time()
            return f'is it running??? {timeLeft} minutes left!', 1
        else:
            return "lottery isn't running!", 0
    elif p_message == '!help':
        reply = "Welcome here. This is a Lottery bot where people play against each other" \
                "\n \n" \
                "type !startLottery to start Lottery" \
                "\n" \
                "type !Lottery to see ongoing Lottery" \
                "\n" \
                "type !result to see the Lottery results" \
                "\n \n" \
                "you can use command without capital letters"

        return reply, 0
    else:
        return 'nah', 0  # meaning it doesn't match with any command


async def send_message(message, user_message, response, emoji, is_private):
    print(user_message)
    try:

        if is_private:
            reply = await message.author.send(response)

        else:
            reply = await message.channel.send(response)

        if emoji == 1:
            await reply.add_reaction('🍓')
            await reply.add_reaction('🍎')
            await reply.add_reaction('🍐')
            await reply.add_reaction('🍌')

            return reply
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

        private = False  # private chat or not?

        if userMessage[0] == '?':
            private = True
            userMessage = userMessage[1:]
        else:
            private = False

        response, emoji = handle_response(userMessage)

        if response == 'nah':
            response = 'what the hell u saying, type !help for commands.'
            reply = await send_message(message, userMessage, response, emoji, is_private=False)
        else:
            reply = await send_message(message, userMessage, response, emoji, is_private=private)

        def check(reaction, user):
            return user == message.author and str(reaction.emoji) == '🍓'

        try:
            reaction, user = await bot.wait_for('reaction_add', timeout=60.0, check=check)
        except asyncio.TimeoutError:
            print('time out')
        else:
            reply = await send_message(message, userMessage, f'{user} reacted sheeesh', 0, is_private=private)




    print(API_TOKEN)
    bot.run(API_TOKEN)


if __name__ == '__main__':
    run_discord_bot()
    print('Bot Stopped')
