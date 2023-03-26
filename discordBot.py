import discord
from discord.ext import commands
from os import environ

bot = commands.Bot(command_prefix='!')

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

@bot.command()
async def hello(ctx):
    await ctx.send('Hello!')

API_TOKEN = environ.get('BotApi')
bot.run(API_TOKEN)
print(API_TOKEN)