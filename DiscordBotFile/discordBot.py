import logging
from typing import Union

import discord
from os import environ
from lottery import Lottery

API_TOKEN = environ.get("BotApi")

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

givenTime = 10  # minutes
lottery = Lottery(time_delta=givenTime)


def handle_response(message) -> Union[tuple[str, int], str]:
    timeLeft = lottery.time_left()

    p_message = message.lower()
    maxVote = lottery.get_max_vote()

    # the value after reply is the emoji status

    if p_message == "!startlottery":
        if timeLeft == 0:
            lottery.start()
            return f"Lottery started! {givenTime} minutes left! \n" \
                   f"You can vote up to {maxVote} fruit", 1
        elif timeLeft < 0:
            winners = lottery.get_winner()
            print(winners)
            winners_str = ", ".join(winners)

            if winners:
                lottery.reset()
                lottery.start()
                return f"The last lottery winners are {winners_str} \n" \
                       f"Lottery started! {givenTime} minutes left!", 1

            else:
                lottery.reset()
                lottery.start()
                return f"No one had won the last lottery!\n" \
                       f"Lottery started! {givenTime} minutes left!", 1

        else:
            return f"lottery is running. {timeLeft} minutes left! \n" \
                   f"You can vote up to {maxVote} fruit", 1

    elif p_message == "!lottery":
        if timeLeft > 0:
            return f"lottery is running. {timeLeft} minutes left! \n" \
                   f"You can vote up to {maxVote} fruit", 1
        elif timeLeft == 0:
            return "lottery isn't running! Start Lottery by typing !startLottery", 0
        else:
            winners = lottery.get_winner()
            winners_str = ", ".join(winners)
            if winners:
                return f"lottery is expired! User {winners_str} had won the Lottery!", 0
            else:
                return "lottery is expired! No one had won the Lottery!", 0

    elif p_message == "!result":
        if timeLeft < 0:
            winners = lottery.get_winner()
            winners_str = ", ".join(winners)
            print(f" winner is {winners}")
            if winners:
                return f"User {winners_str} had won the Lottery!", 0
            else:
                return "No one had won the Lottery!", 0
        elif timeLeft == 0:
            return "lottery isn't running! Start Lottery by typing !startLottery", 0
        else:
            return f"lottery is running. {timeLeft} minutes left! \n" \
                   f"You can vote up to {maxVote} fruit", 1

    elif p_message == "!help":
        reply = (
            "Welcome here. This is a Lottery bot where people play against each other"
            "\n \n"
            "type !startLottery to start Lottery"
            "\n"
            "type !Lottery to see ongoing Lottery"
            "\n"
            "type !result to see the Lottery results"
            "\n \n"
            "you can use command without capital letters"
        )

        return reply, 0
    else:
        return "nah", 0  # meaning it doesn't match with any command


async def send_message(message, user_message, response, emoji, is_private):
    try:
        if is_private:
            reply = await message.author.send(response)

        else:
            reply = await message.channel.send(response)

        if emoji == 1:
            emojiDict = lottery.get_emoji_dict()
            for emoji in emojiDict.keys():
                await reply.add_reaction(emoji)

        return reply
    except Exception as e:
        print(e)


@bot.event
async def on_ready():
    print(f"{bot.user} is now running")
    print("Logged in as")
    print(bot.user.name)
    print(bot.user.id)
    print("------")


@bot.event
async def on_message(message):
    if not message.content.startswith('!'):
        return

    if message.author == bot.user:
        return

    username = str(message.author)
    userMessage = str(message.content)
    channel = str(message.channel)
    print(f"{username} said {userMessage} in {channel}")

    private = False  # private chat or not?

    if userMessage[0] == "?":
        private = True
        userMessage = userMessage[1:]

    response, emoji = handle_response(userMessage)

    if response == "nah":
        response = "what the hell u saying, type !help for commands."
        await send_message(message, userMessage, response, emoji, is_private=private)
    else:
        await send_message(message, userMessage, response, emoji, is_private=private)


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
        message = reaction.message

        timeLeft = lottery.time_left()

        if timeLeft <= 0:
            await sent("The time is up!")
            return

        emojiDict = lottery.get_emoji_dict()
        weirdEmoji = False
        reaction = emojiDict.get(reaction.emoji)
        maxVote = lottery.get_max_vote()

        if reaction is None:
            weirdEmoji = True

        if not weirdEmoji:
            userVote = lottery.get_user_vote(username)
            vote_count = len(userVote)
            sameFruitVote = userVote.get(reaction, 0)

            maxVotes = lottery.get_max_vote()

            if sameFruitVote == 1:
                response = f"You can vote up to {maxVote} fruit" \
                           f"{user.name}, you already voted this fruit!"
                await message.edit(content=response)

            elif vote_count < maxVotes and sameFruitVote == 0:
                response = f"You can vote up to {maxVote} fruit" \
                           f"{user} voted {reaction}"
                await message.edit(content=response)
                lottery.store_vote(reaction, username)

            else:
                response = f"You can vote up to {maxVote} fruit" \
                           f"{user.name}, you already voted 3 fruit!"
                await message.edit(content=response)
    else:
        logging.warning("This function doesn't work in private messages!")


if __name__ == "__main__":
    print(API_TOKEN)
    bot.run(API_TOKEN)
    print("Bot Stopped")
