import os
import discord
import random
import argparse
from datetime import datetime
import pytz
import data
import sys
import asyncio
import pickledb
from dotenv import load_dotenv
from discord.ext import commands, tasks

# Predefined constants
DEFAULT_MINE_REFRESH_INTERVAL = 259200
DEFAULT_MINE_NOTIFY_INTERVAL = 1800

# Handle command line arguments
parser = argparse.ArgumentParser(description="Discord bot for Genshin")
parser.add_argument('-t', '--test', dest='test',
                    action='store_true', help="test mode")
parser.add_argument('-m', '--mine', dest='mine', nargs='?',
                    type=int, const=DEFAULT_MINE_REFRESH_INTERVAL, default=DEFAULT_MINE_REFRESH_INTERVAL, help="mine refresh interval in seconds")
parser.add_argument('-n', '--notify', dest='mine_notify_interval', nargs='?',
                    type=int, const=DEFAULT_MINE_NOTIFY_INTERVAL, default=DEFAULT_MINE_NOTIFY_INTERVAL, help="mine notify interval in seconds")
args = parser.parse_args()

# Constants
load_dotenv()
IF_TEST = args.test
TOKEN = os.getenv('DISCORD_TOKEN')
DICE_LIMIT = 100
MINE_REFRESH_INTERVAL = args.mine
MINE_NOTIFY_INTERVAL = args.mine_notify_interval
TELL = "tell"
CANCEL = "cancel"
SELF = "self"
LIST = "list"
CURSE = "我:sunny:死你的:horse:"
weekay_reprs = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]

# Initialization
command_prefix = ""
if IF_TEST:
    command_prefix = "="
else:
    command_prefix = "+"

intents = discord.Intents.default()
intents.typing = False
intents.presences = False
intents.members = True

bot = commands.Bot(command_prefix=command_prefix, intents=intents)

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
        await ctx.send("{} {}，这数合不合理你自己没点逼数吗".format(
            ctx.message.author.mention, CURSE))
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
        await ctx.send("{} {}，一周有几天需要我教你吗？".format(ctx.message.author.mention, CURSE))
        return

    # Get the correct weekday in game, if not specified by user
    weekday_today = weekday
    today = ""
    if weekday_today == -1:
        today = "（今天）"
        chinaTimezone = pytz.timezone("Asia/Shanghai")
        utc_now = pytz.utc.localize(datetime.utcnow())
        date_timezone = utc_now.replace(
            tzinfo=pytz.utc).astimezone(chinaTimezone)
        weekday_today = date_timezone.weekday()
        if date_timezone.hour < 4:
            weekday_today = (weekday_today - 1 + 7) % 7

    # Format response
    response = ""
    characters_today = characters[weekday_today]
    weapons_today = weapons[weekday_today]
    if len(characters_today) <= 0 and len(weapons_today) <= 0:
        response = "{} {}{}刷个锤子".format(
            ctx.message.author.mention, weekay_reprs[weekday_today], today)
    else:
        response = "{} {}{}".format(
            ctx.message.author.mention, weekay_reprs[weekday_today], today)
        if len(characters_today) > 0:
            response += "要刷天赋的角色是：{}。".format("，".join(characters_today))
        if len(weapons_today) > 0:
            response += "要刷材料的武器是：{}。".format("，".join(weapons_today))

    await ctx.send(response)


@bot.command(name="mine", help="Tell me you\'ve mined today! I\'ll notify you when it's ready again")
async def mine(ctx, sub_command: str = "tell", char_name: str = "self", notify_time: int = MINE_REFRESH_INTERVAL):
    # Decide if the arguments are valid
    available_sub_commands = [TELL, CANCEL, LIST]
    if sub_command not in available_sub_commands:
        raise commands.errors.CommandNotFound

    response = ""
    key = "{}.{}".format(str(ctx.message.author.id), char_name)
    record = mine_db.lgetall(key) if mine_db.exists(key) else None

    char_repr = "你"
    if char_name != SELF:
        char_repr = char_name

    # Check if the user is requesting a cancellation
    if sub_command == CANCEL:
        if record:
            mine_db.lremlist(key)
            response = "{} 已经取消了{}的记录".format(
                ctx.message.author.mention, char_repr)
        else:
            response = "{} {}，你说过{}挖矿吗".format(
                ctx.message.author.mention, CURSE, char_repr)
        await ctx.send(response)

    elif sub_command == TELL:
        # Check if the user has already reported
        if record:
            # Calculate delta time
            _, record_time = record
            current_datetime = datetime.now()
            start_datetime = datetime.strptime(
                record_time, "%Y-%m-%d %H:%M:%S.%f")
            delta_datetime = current_datetime - start_datetime
            total_seconds = delta_datetime.total_seconds()
            mins = (total_seconds // 60) % 60
            hours = (total_seconds // 3600) % 24
            days = total_seconds // 86400
            time_repr = "{}分钟".format(int(mins))
            if hours > 0:
                time_repr = "{}小时".format(int(hours)) + time_repr
            if days > 0:
                time_repr = "{}天".format(int(days)) + time_repr

            response = "{} {}，你不是在{}前说过{}挖矿了吗".format(
                ctx.message.author.mention, CURSE, time_repr, char_repr)
            await ctx.send(response)
        else:
            # Add a new entry
            response = "{} 知道{}今天挖矿了".format(
                ctx.message.author.mention, char_repr)

            # record format: (channel id, time)
            mine_db.lcreate(key)
            mine_db.ladd(key, str(ctx.message.channel.id))
            mine_db.ladd(key, str(datetime.now()))
            await ctx.send(response)

    elif sub_command == LIST:
        response = "没人挖过矿"

        keys = list(mine_db.getall())
        if len(keys) > 0:
            response = "挖矿日程"
            for key in keys:
                if mine_db.exists(key):
                    # Get necessary information
                    user_id, char_name = key.split(".")
                    user = bot.get_user(int(user_id))
                    display_name = user.display_name
                    channel_id, datetime_string = mine_db.lgetall(key)
                    channel = bot.get_channel(int(channel_id))
                    if type(channel) != discord.DMChannel:
                        guild = channel.guild
                        if guild:
                            member = guild.get_member(int(user_id))
                            display_name = member.nick

                    # Calculate delta time
                    current_datetime = datetime.now()
                    start_datetime = datetime.strptime(
                        datetime_string, "%Y-%m-%d %H:%M:%S.%f")
                    delta_datetime = current_datetime - start_datetime
                    total_seconds = MINE_REFRESH_INTERVAL - delta_datetime.total_seconds()
                    mins = (total_seconds // 60) % 60
                    hours = (total_seconds // 3600) % 24
                    days = total_seconds // 86400
                    time_repr = "{}分钟".format(int(mins))
                    if hours > 0:
                        time_repr = "{}小时".format(int(hours)) + time_repr
                    if days > 0:
                        time_repr = "{}天".format(int(days)) + time_repr

                    # Append
                    char_repr = ""
                    if char_name != SELF:
                        char_repr = "-"+char_name
                    response += "\n{}{}：还剩{}".format(
                        display_name, char_repr, time_repr)
        await ctx.send(response)


@tasks.loop(seconds=MINE_NOTIFY_INTERVAL)
async def mine_notify():
    await bot.wait_until_ready()

    keys = list(mine_db.getall())
    for key in keys:
        if mine_db.exists(key):
            # Get necessary information
            user_id, char_name = key.split(".")
            channel_id, datetime_string = mine_db.lgetall(key)
            user = bot.get_user(int(user_id))
            channel = bot.get_channel(int(channel_id))

            # Only proceed when both channel and user are available
            if user and channel:
                # Determine if it's time to notify
                current_datetime = datetime.now()
                start_datetime = datetime.strptime(
                    datetime_string, "%Y-%m-%d %H:%M:%S.%f")
                delta_datetime = current_datetime - start_datetime
                diff_seconds = delta_datetime.total_seconds()
                if diff_seconds <= MINE_REFRESH_INTERVAL:
                    continue

                # Notify
                char_repr = "你"
                if char_name != SELF:
                    char_repr = char_name
                response = "{} {}又可以挖矿了".format(user.mention, char_repr)
                await channel.send(response)
                mine_db.lremlist(key)
            else:
                mine_db.lremlist(key)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CommandNotFound):
        await ctx.send("{} {}，不会用别用".format(ctx.message.author.mention, CURSE))
    else:
        if IF_TEST:
            await ctx.send("{} {}，给我整晕了: {}".format(ctx.message.author.mention, CURSE, error))
        else:
            await ctx.send("{} {}，给我整晕了".format(ctx.message.author.mention, CURSE))

# The main routine of the bot
mine_notify.start()
bot.run(TOKEN)
