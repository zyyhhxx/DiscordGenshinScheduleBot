import os
import discord
import random
from datetime import datetime
import pytz
import getopt
import data
import sys
import asyncio
import pickledb
from dotenv import load_dotenv
from discord.ext import commands

# Constants
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
DICE_LIMIT = 100
weekay_reprs = ["星期一","星期二","星期三","星期四","星期五","星期六","星期日"]

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
weapons = data.readWeeklyData("weapon.json")
mine_db = pickledb.load('mine.db', True)

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
async def work(ctx, weekday: int = -1):
    if weekday > 6 or weekday < -1:
        await ctx.send("{} 我:sunny:死你的:horse:，一周有几天需要我教你吗？".format(ctx.message.author.mention))
        return

    # Get the correct weekday in game, if not specified by user
    weekday_today = weekday
    if weekday_today == -1:
        chinaTimezone = pytz.timezone("Asia/Shanghai")
        utc_now = pytz.utc.localize(datetime.utcnow())
        date_timezone = utc_now.replace(tzinfo=pytz.utc).astimezone(chinaTimezone)
        weekday_today = date_timezone.weekday()
        if date_timezone.hour < 4:
            weekday_today = (weekday_today - 1 + 7) % 7

    # Format response
    response = ""
    characters_today = characters[weekday_today]
    weapons_today = weapons[weekday_today]
    if len(characters_today) <= 0 and len(weapons_today) <= 0:
        response = "{} {}刷个锤子".format(ctx.message.author.mention, weekay_reprs[weekday_today])
    else:
        response = "{} {}".format(ctx.message.author.mention, weekay_reprs[weekday_today])
        if len(characters_today) > 0:
            response += " 要刷天赋的角色是： {}".format("，".join(characters_today))
        if len(weapons_today) > 0:
            response += " 要刷材料的武器是： {}".format("，".join(weapons_today))
      
    await ctx.send(response)

@bot.command(name="mine", help="Tell me you\'ve mined today! I\'ll notify you when it's ready again")
async def mine(ctx, sub_command:str="tell"):
    TELL = "tell"
    CANCEL = "cancel"
    available_sub_commands = [TELL, CANCEL]
    if sub_command not in available_sub_commands:
        raise commands.errors.CommandNotFound

    response = ""
    record = mine_db.get(str(ctx.message.author.id))

    # Check if the user is requesting a cancellation
    if sub_command == CANCEL:
        if record:
            mine_db.rem(str(ctx.message.author.id))
            response = "{} 已经取消了".format(ctx.message.author.mention)
        else:
            response = "{} 我:sunny:死你的:horse:，你说过挖矿吗".format(ctx.message.author.mention)
        await ctx.send(response)

    elif sub_command == TELL:
        # Check if the user has already reported
        if record:
            response = "{} 我:sunny:死你的:horse:，你不是在{}说过了吗".format(ctx.message.author.mention,
                record)
            await ctx.send(response)
        else:
            response = "{} 知道你今天挖矿了".format(ctx.message.author.mention)
            mine_db.set(str(ctx.message.author.id), str(datetime.now()))
            await ctx.send(response)
            await asyncio.sleep(259200)

            # Only notify when still available
            record = mine_db.get(str(ctx.message.author.id))
            if record:
                response = "{} 又可以挖矿了".format(ctx.message.author.mention)
                await ctx.send(response)
                mine_db.rem(str(ctx.message.author.id))


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CommandNotFound):
        await ctx.send("{} 我:sunny:死你的:horse:，不会用别用".format(ctx.message.author.mention))
    else:
        if if_test:
            await ctx.send("{} 我:sunny:死你的:horse:，给我整晕了: {}".format(ctx.message.author.mention, error))
        else:
            await ctx.send("{} 我:sunny:死你的:horse:，给我整晕了".format(ctx.message.author.mention))

bot.run(TOKEN)
