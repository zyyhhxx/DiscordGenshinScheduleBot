# bot.py
import os

import discord
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

client = discord.Client()

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content == '!init':
        response = "Hello World!"
        await message.channel.send(response)

client.run(TOKEN)