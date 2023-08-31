import os
import discord
from dotenv import load_dotenv
from discord.ext import commands
import requests

# Credentials
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Create bot
intents = discord.Intents.all();
client = commands.Bot(command_prefix='!', intents=intents)

# Startup Information
@client.event
async def on_ready():
    print('Connected to bot: {}'.format(client.user.name))
    print('Bot ID: {}'.format(client.user.id))

# Command
@client.command(name='mybag', help='Retreives the details of your current main disc golf bag.')
async def mybag(ctx):
    print(ctx.message.author.id)
    await ctx.send(f'Bags are not yet configured. Please check back later.')   
    
# Run the bot
client.run(TOKEN)