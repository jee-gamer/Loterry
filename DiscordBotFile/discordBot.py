from typing import Union

import discord
from os import environ
from lottery import Lottery
import time
import asyncio

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

givenTime = 30  # seconds
lottery = Lottery(time_delta=givenTime)


def handle_response(message, username) -> Union[tuple[str, int], str]:
    timeLeft = lottery.time_left()

    p_message = message.lower()
    print(f'He said {p_message}')

    # the value after reply is the emoji status
    global lotteryStart
    maxVotes = lottery.get_max_vote()

    if p_message == '!startlottery':
        if timeLeft == 0:
            lottery.start()
            return "Lottery started"

    elif p_message == '!lottery':
        if timeLeft > 0:
            return f'lottery is running. {timeLeft} seconds left!, please vote in {givenTime - timeLeft} minute', 1
        elif timeLeft == 0:
            return "lottery isn't running! Start Lottery", 0
        else:
            return "lottery is expired! Print results", 0

    elif p_message == '!result':
        if timeLeft < 0:
            winners = lottery.get_winner()
            winners_str = ", ".join(winners)
            return f"User {winners_str} had won the Lottery!"
        elif timeLeft == 0:
            return "lottery isn't running! Start Lottery", 0
        else:
            return f'lottery is running. {timeLeft} seconds left!, please vote in {givenTime - timeLeft} minute', 1

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

        response, emoji = handle_response(userMessage, username)

        if response == 'nah':
            response = 'what the hell u saying, type !help for commands.'
            reply = await send_message(message, userMessage, response, emoji, is_private=False)
        else:
            reply = await send_message(message, userMessage, response, emoji, is_private=private)

    @bot.event
    async def on_reaction_add(reaction, user):

        if user == bot.user:
            return

        if reaction.message.guild is not None:
            # Reaction added in a guild
            channel = reaction.message.channel
            sent = channel.send
            username = user.name + "#" + user.discriminator
            print(username)

            if lotteryStart == 0:
                await sent('The lottery have not started!')
                return
            elif lottery.end_lottery():
                await sent('The lottery is not running!')
                return

            weirdEmoji = False
            if reaction.emoji == '🍓':
                reaction = 'strawberry'
            elif reaction.emoji == "🍎":
                reaction = 'apple'
            elif reaction.emoji == "🍐":
                reaction = 'pear'
            elif reaction.emoji == "🍌":
                reaction = 'banana'
            else:
                weirdEmoji = True

            if not weirdEmoji:

                userVote = lottery.get_user_vote(username)

                vote_count = len(userVote)

                sameFruitVote = userVote.get(reaction, 0)

                maxVotes = lottery.get_max_vote()

                if sameFruitVote == 1:
                    response = ', you already voted this fruit!'
                    reply = await sent(user.name + response)

                elif vote_count < maxVotes and sameFruitVote == 0:
                    response = f'{user} voted {reaction}'
                    reply = await sent(response)
                    lottery.store_vote(reaction, username)

                else:
                    response = ', you already voted 3 fruit!'
                    reply = await sent(user.name + response)
        else:
            print('shit doesnt work in private message dawg')

    print(API_TOKEN)
    bot.run(API_TOKEN)


if __name__ == '__main__':
    run_discord_bot()
    print('Bot Stopped')
