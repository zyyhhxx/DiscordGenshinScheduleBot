import os
import discord
import random
import datetime
import pytz
import getopt
import data
import sys
from dotenv import load_dotenv
from discord.ext import commands

# Constants
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
DICE_LIMIT = 100

# Global variables
if_test = False

# Handle command line arguments
opts, args = getopt.getopt(sys.argv[1:], "t", [])
for opt, arg in opts:
    if opt == "-t":
        if_test = True

# Initialization
command_prefix = ""
if if_test:
    command_prefix = "="
else:
    command_prefix = "+"
bot = commands.Bot(command_prefix=command_prefix)

# Read data
characters = data.readWeeklyData("character.json")

###############
# Bot Commands
###############


@bot.command(name="init", help='The First thing a program has to say')
async def hello_world(ctx):
    response = "Hello World!"
    await ctx.send(response)


@bot.command(name='roll', help='Roll one (or more) dice')
async def roll(ctx, number_of_dice: int = 1, number_of_sides: int = 6):
    if number_of_dice <= 0 or number_of_dice > DICE_LIMIT or number_of_sides > DICE_LIMIT:
        await ctx.send("{} 我:sunny:死你的:horse:，这数合不合理你自己没点逼数吗".format(
            ctx.message.author.mention))
    else:
        dice = [
            str(random.choice(range(1, number_of_sides + 1)))
            for _ in range(number_of_dice)
        ]
        await ctx.send("{} Dice: {}".format(ctx.message.author.mention,
                                            ', '.join(dice)))


@bot.command(name="work", help='Today\'s work')
async def work(ctx):
    # Get the correct weekday in game
    chinaTimezone = pytz.timezone("Asia/Shanghai")
    utc_now = pytz.utc.localize(datetime.datetime.utcnow())
    date_timezone = utc_now.replace(tzinfo=pytz.utc).astimezone(chinaTimezone)
    weekday_today = date_timezone.weekday()
    if date_timezone.hour < 4:
        weekday_today = (weekday_today - 1 + 7) % 7

    # Format response
    response = ""
    characters_today = characters[weekday_today]
    if len(characters_today) <= 0:
        response = "{} 今天刷个锤子".format(ctx.message.author.mention)
    else:
        response = "{} 今天要刷天赋的角色是： {}".format(ctx.message.author.mention,
                                              "，".join(characters_today))
    await ctx.send(response)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CommandNotFound):
        await ctx.send("{} 我:sunny:死你的:horse:，不会用别用".format(ctx.message.author.mention))
    else:
        await ctx.send("{} 我:sunny:死你的:horse:，给我整晕了".format(ctx.message.author.mention))

bot.run(TOKEN)
