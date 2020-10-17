import os
import discord
import random
import argparse
from datetime import datetime
import pytz
import sys
import asyncio
import pickledb
from dotenv import load_dotenv
from discord.ext import commands, tasks
from beautifultable import BeautifulTable

import gacha
import data
import language
import mine

# Predefined constants
LANGUAGE = "zh_s"
TIME = "time"
CHANNEL = "channel"

# Handle command line arguments
parser = argparse.ArgumentParser(description="Discord bot for Genshin")
parser.add_argument('-t', '--test', dest='test',
                    action='store_true', help="test mode")
parser.add_argument('-m', '--mine', dest='mine', nargs='?',
                    type=int, const=mine.DEFAULT_MINE_REFRESH_INTERVAL, default=mine.DEFAULT_MINE_REFRESH_INTERVAL, help="mine refresh interval in seconds")
parser.add_argument('-n', '--notify', dest='mine_notify_interval', nargs='?',
                    type=int, const=mine.DEFAULT_MINE_NOTIFY_INTERVAL, default=mine.DEFAULT_MINE_NOTIFY_INTERVAL, help="mine notify interval in seconds")
args = parser.parse_args()

# Constants
load_dotenv()
IF_TEST = args.test
TOKEN = os.getenv('DISCORD_TOKEN')
DICE_LIMIT = 100
MINE_REFRESH_INTERVAL = args.mine
MINE_NOTIFY_INTERVAL = args.mine_notify_interval
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
global gacha_channel_id
gacha_channel_id = 0

# Read data
characters = data.readWeeklyData("character.json")
weapons = data.readWeeklyData("weapon.json")
mine_db = pickledb.load('mine.db', True)
gacha_db = pickledb.load('gacha.db', True)

###############
# Bot Commands
###############


@bot.command(name='roll', aliases=["r"], help='Roll one (or more) dice')
async def roll(ctx, number_of_dice: int = 1, number_of_sides: int = 6):
    if number_of_dice <= 0 or number_of_dice > DICE_LIMIT or number_of_sides > DICE_LIMIT:
        await ctx.send("{} {}，这数合不合理你自己没点逼数吗".format(
            ctx.message.author.mention, language.CURSE))
    else:
        dice = [
            str(random.choice(range(1, number_of_sides + 1)))
            for _ in range(number_of_dice)
        ]
        await ctx.send("{} Dice: {}".format(ctx.message.author.mention,
                                            ', '.join(dice)))


@bot.command(name="work", aliases=["w"], help='Today\'s work')
async def work(ctx, weekday: int = -1):
    if weekday > 6 or weekday < -1:
        await ctx.send("{} {}，一周有几天需要我教你吗？".format(ctx.message.author.mention, language.CURSE))
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


@bot.group(name="mine", aliases=["m"],
           help="Tell me you\'ve mined today! I\'ll notify you when it's ready again")
async def mine_command(ctx):
    if not ctx.invoked_subcommand:
        await ctx.invoke(mine_tell)


@mine_command.command(name="tell", aliases=["t"], help="Tell the bot you've mined today")
async def mine_tell(ctx, char_name: str = mine.SELF, notify_time: int = MINE_REFRESH_INTERVAL):
    response = ""
    key = "{}.{}".format(str(ctx.message.author.id), char_name)
    record = mine_db.get(key) if mine_db.exists(key) else None
    char_repr = mine.get_char_repr(char_name, LANGUAGE)

    # Check if the user has already reported
    if record:
        # Calculate delta time
        datetime_string = record[TIME]
        time_repr = mine.get_time_repr(datetime_string, True, LANGUAGE)

        response = "{} {}，你不是在{}前说过{}挖矿了吗".format(
            ctx.message.author.mention, language.CURSE, time_repr, char_repr)
    else:
        # Add a new entry
        response = "{} 知道{}今天挖矿了".format(
            ctx.message.author.mention, char_repr)

        record = {
            CHANNEL: str(ctx.message.channel.id),
            TIME: str(datetime.now())
        }
        mine_db.set(key, record)
    await ctx.send(response)


@mine_command.command(name="cancel", aliases=["c"], help="Cancel your mine record")
async def mine_cancel(ctx, char_name: str = mine.SELF):
    response = ""
    key = "{}.{}".format(str(ctx.message.author.id), char_name)
    record = mine_db.get(key) if mine_db.exists(key) else None
    char_repr = mine.get_char_repr(char_name, LANGUAGE)

    if record:
        mine_db.rem(key)
        response = "{} 已经取消了{}的记录".format(
            ctx.message.author.mention, char_repr)
    else:
        response = "{} {}，你说过{}挖矿吗".format(
            ctx.message.author.mention, language.CURSE, char_repr)
    await ctx.send(response)


@mine_command.command(name="list", aliases=["l"], help="List all mining records")
async def mine_list(ctx, char_name: str = mine.SELF):
    key = "{}.{}".format(str(ctx.message.author.id), char_name)
    char_repr = mine.get_char_repr(char_name, LANGUAGE)
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
                record = mine_db.get(key)
                channel_id, datetime_string = record[CHANNEL], record[TIME]
                channel = bot.get_channel(int(channel_id))
                if type(channel) != discord.DMChannel:
                    guild = channel.guild
                    if guild:
                        member = guild.get_member(int(user_id))
                        display_name = member.nick

                # Calculate delta time
                time_repr = mine.get_time_repr(
                    datetime_string, False, LANGUAGE)

                # Append
                char_repr = ""
                if char_name != mine.SELF:
                    char_repr = "-"+char_name
                response += "\n{}{}：还剩{}".format(
                    display_name, char_repr, time_repr)
    await ctx.send(response)


@bot.group(name="gacha", aliases=["g"], help="Gacha!")
async def gacha_command(ctx):
    if not ctx.invoked_subcommand:
        can_gacha, message = gacha.check_gacha_channel(ctx, bot.get_channel(gacha_channel_id))
        if not can_gacha:
            await ctx.send("{} {}".format(ctx.message.author.mention, message))
            return

        await ctx.invoke(gacha_pull)


@gacha_command.command(name="pull", aliases=["p"], help="Try your luck with gacha!")
async def gacha_pull(ctx, num: int = 10, wish: int = 0):
    can_gacha, message = gacha.check_gacha_channel(ctx, bot.get_channel(gacha_channel_id))
    if not can_gacha:
        await ctx.send("{} {}".format(ctx.message.author.mention, message))
        return

    user_id = str(ctx.message.author.id)
    # Check the input
    if num > 1000:
        num = 1000
    elif num < 1:
        num = 1

    # Get the base counts of gacha
    total_count = 0
    five_star_count = 0
    four_star_count = 0
    five_star_base = 0
    four_star_base = 0
    items = {}
    user_data = {"five_star_base": five_star_base,
                 "four_star_base": four_star_base,
                 "total_count": total_count,
                 "five_star_count": five_star_count,
                 "four_star_count": four_star_count,
                 "items": items
                 }
    if user_id in gacha_db.getall():
        user_data = gacha_db.get(user_id)
        five_star_base = user_data["five_star_base"]
        four_star_base = user_data["four_star_base"]
        total_count = user_data["total_count"]
        five_star_count = user_data["five_star_count"]
        four_star_count = user_data["four_star_count"]
        items = user_data["items"]

    # Pull from the pool
    results = []
    for _ in range(num):
        result, outcome_pool = gacha.pull(wish, five_star_base, four_star_base)
        total_count += 1
        five_star_base += 1
        four_star_base += 1
        if outcome_pool == 5:
            five_star_base = 0
            four_star_base = 0
            five_star_count += 1
        elif outcome_pool == 4:
            four_star_base = 0
            four_star_count += 1
        if outcome_pool > 3:
            if result not in items:
                items[result] = 1
            else:
                items[result] += 1
        if num > 10:
            if outcome_pool > 3:
                results.append(result)
        else:
            results.append(result)

    # Save the base counts of gacha
    user_data["five_star_base"] = five_star_base
    user_data["four_star_base"] = four_star_base
    user_data["total_count"] = total_count
    user_data["five_star_count"] = five_star_count
    user_data["four_star_count"] = four_star_count
    user_data["items"] = items
    gacha_db.set(user_id, user_data)

    # Tell the user
    message = "{}{}发抽卡结果".format(language.get_word(
        gacha.wishes[wish]["name"], LANGUAGE), num)
    if num <= 10 and five_star_count > 0 and five_star_base >= 10:
        message += "\n距离上次五星出货：{}".format(five_star_base)
    table = BeautifulTable()
    table.set_style(BeautifulTable.STYLE_NONE)
    table.columns.alignment = BeautifulTable.ALIGN_LEFT
    if num <= 10:
        for i in range(len(results)):
            word = language.get_word(results[i], LANGUAGE)
            rarity = data.get_rarity(results[i])
            rarity_repr = rarity*":star:"
            if rarity >= 5:
                word = "**{}**".format(word)
            table.rows.append([rarity_repr, word])
        message += "\n" + str(table)
    else:
        # Put all results into a dictionary to count
        count_results = {}
        for i in range(len(results)):
            if results[i] in count_results:
                count_results[results[i]] += 1
            else:
                count_results[results[i]] = 1

        # Then display the counts
        items_stats = {}
        items_stats[5] = {}
        items_stats[4] = {}
        for key in count_results:
            rarity = data.get_rarity(key)
            items_stats[rarity][key] = count_results[key]
        for key in items_stats[5]:
            message += "\n{}{} ✕ {}".format(":star:"*5,
                                            language.get_word(key, LANGUAGE), items_stats[5][key])
        for key in items_stats[4]:
            message += "\n{}{} ✕ {}".format(":star:"*4,
                                            language.get_word(key, LANGUAGE), items_stats[4][key])

    await ctx.send("{} {}".format(ctx.message.author.mention, message))


@gacha_command.command(name="reset", aliases=["r"], help="Reset your gacha record")
async def gacha_reset(ctx):
    can_gacha, message = gacha.check_gacha_channel(ctx, bot.get_channel(gacha_channel_id))
    if not can_gacha:
        await ctx.send("{} {}".format(ctx.message.author.mention, message))
        return

    user_id = str(ctx.message.author.id)
    gacha_db.rem(user_id)
    message = "已经重置你的抽卡记录"
    await ctx.send("{} {}".format(ctx.message.author.mention, message))


@gacha_command.group(name="stats", aliases=["s"], help="Show your gacha stats")
async def gacha_stats(ctx):
    if not ctx.invoked_subcommand:
        can_gacha, message = gacha.check_gacha_channel(ctx, bot.get_channel(gacha_channel_id))
        if not can_gacha:
            await ctx.send("{} {}".format(ctx.message.author.mention, message))
            return

        user_id = str(ctx.message.author.id)
        if user_id in gacha_db.getall():
            # Get the information
            user_data = gacha_db.get(user_id)
            total_count = user_data["total_count"]
            five_star_count = user_data["five_star_count"]
            four_star_count = user_data["four_star_count"]

            # Calculate related stats
            five_star_rate = round(five_star_count / total_count * 100, 2)
            four_star_rate = round(four_star_count / total_count * 100, 2)

            message = "抽卡记录\n你总共抽了{}发，花了{}元\n五星出货率为{}%，四星出货率为{}%".format(
                total_count, total_count*16, five_star_rate, four_star_rate)
            await ctx.send("{} {}".format(ctx.message.author.mention, message))

        else:
            message = "没有你的记录"
            await ctx.send("{} {}".format(ctx.message.author.mention, message))


@gacha_stats.command(name="items", aliases=["i"],
                     help="Show your gacha stats with items")
async def gacha_stats_items(ctx):
    can_gacha, message = gacha.check_gacha_channel(ctx, bot.get_channel(gacha_channel_id))
    if not can_gacha:
        await ctx.send("{} {}".format(ctx.message.author.mention, message))
        return

    user_id = str(ctx.message.author.id)
    if user_id in gacha_db.getall():
        # Get the information
        user_data = gacha_db.get(user_id)
        total_count = user_data["total_count"]
        five_star_count = user_data["five_star_count"]
        four_star_count = user_data["four_star_count"]
        items = user_data["items"]

        items_stats = {}
        items_stats[5] = []
        items_stats[4] = []
        for key in items:
            rarity = data.get_rarity(key)
            items_stats[rarity].append({"name": key, "count": items[key]})
        items_stats[5].sort(key=lambda item: item["count"], reverse=True)
        items_stats[4].sort(key=lambda item: item["count"], reverse=True)

        message = "抽卡记录\n你总共抽了{}发，花了{}元\n获得五星{}个，四星{}个".format(
            total_count, total_count*16, five_star_count, four_star_count)
        for item in items_stats[5]:
            message += "\n{}{} ✕ {}".format(":star:"*5,
                                            language.get_word(item["name"], LANGUAGE), item["count"])
        for item in items_stats[4]:
            message += "\n{}{} ✕ {}".format(":star:"*4,
                                            language.get_word(item["name"], LANGUAGE), item["count"])

        await ctx.send("{} {}".format(ctx.message.author.mention, message))

    else:
        message = "没有你的记录"
        await ctx.send("{} {}".format(ctx.message.author.mention, message))

@gacha_command.command(name="set", help="Set the current channel as the gacha channel")
async def gacha_set(ctx):
    global gacha_channel_id
    gacha_channel_id = ctx.message.channel.id
    message = "已将本频道设为抽卡频道"
    await ctx.send("{} {}".format(ctx.message.author.mention, message))

@tasks.loop(seconds=MINE_NOTIFY_INTERVAL)
async def mine_notify():
    await bot.wait_until_ready()

    keys = list(mine_db.getall())
    for key in keys:
        if mine_db.exists(key):
            # Get necessary information
            user_id, char_name = key.split(".")
            record = mine_db.get(key)
            channel_id, datetime_string = record[CHANNEL], record[TIME]
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
                char_repr = mine.get_char_repr(char_name, LANGUAGE)
                response = "{} {}又可以挖矿了".format(user.mention, char_repr)
                await channel.send(response)
                mine_db.rem(key)
            else:
                mine_db.rem(key)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CommandNotFound):
        await ctx.send("{} {}，不会用别用".format(ctx.message.author.mention, language.CURSE))
    else:
        if IF_TEST:
            await ctx.send("{} {}，给我整晕了: {}".format(ctx.message.author.mention, language.CURSE, error))
        else:
            await ctx.send("{} {}，给我整晕了".format(ctx.message.author.mention, language.CURSE))

# The main routine of the bot
mine_notify.start()
bot.run(TOKEN)
