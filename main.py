import os
import discord
from dotenv import load_dotenv
from discord.ext import commands
import requests
import sqlite3
import mysql.connector

# Credentials
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
USER = os.getenv('RDS_USER')
PASS = os.getenv('RDS_PASSWORD')
HOST = os.getenv('RDS_HOST')

# print(HOST)
# print(USER)

# Create bot
intents = discord.Intents.all();
bot = commands.Bot(command_prefix='!', intents=intents)

#conn = mysql.connector.connect(db_config)
conn = mysql.connector.connect(
    host=HOST,
    user=USER,
    password=PASS,
    database='discgolfdb'
)
cursor = conn.cursor()
# Create a table to store user bags
cursor.execute('''CREATE TABLE IF NOT EXISTS bags (
                user_id TEXT,
                disc_name TEXT,
                brand TEXT,
                plastic TEXT,
                speed REAL,
                glide REAL,
                turn REAL,
                fade REAL
                )''')
conn.commit()


# # Connect to the SQLite database
# conn = sqlite3.connect('bag_data.db')
# cursor = conn.cursor()



# Startup Information
@bot.event
async def on_ready():
    print('Connected to bot: {}'.format(bot.user.name))
    print('Bot ID: {}'.format(bot.user.id))


# Function to format and display a user's bag as an embedded message
def format_bag(user_id, ctx):
    try:
        cursor.execute('''SELECT * FROM bags WHERE user_id = %s''', (user_id,))
        bag_data = cursor.fetchall()

        if not bag_data:
            return discord.Embed(description="Your bag is empty.")

        bag = {
            'Distance Drivers': [],
            'Fairway Drivers': [],
            'Mid-Ranges': [],
            'Putt/Approach': []
        }

        for disc in bag_data:
            speed = disc[4]
            if speed > 8:
                bag['Distance Drivers'].append(disc[1])  # Add disc name to the category
            elif speed > 5:
                bag['Fairway Drivers'].append(disc[1])
            elif speed > 4:
                bag['Mid-Ranges'].append(disc[1])
            else:
                bag['Putt/Approach'].append(disc[1])

        embed = discord.Embed(title=f"{ctx.author.display_name}'s Bag")
        embed.set_thumbnail(url=ctx.author.avatar.url)  # Set thumbnail as user's profile picture

        for category, discs in bag.items():
            if discs:
                embed.add_field(name=category, value=', '.join(discs), inline=False)  # Add a field for each category

        return embed
    except Exception as e:
        return discord.Embed(description=f"An error occurred: {str(e)}")

# Command to display user's bag
@bot.command(name='mybag')
async def mybag(ctx):
    try:
        user_id = ctx.author.id
        embed = format_bag(user_id, ctx)

        # Send the embedded message
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")

# Function to format and display a user's bag with details in an embedded message
def format_bag_detailed(user_id, ctx):
    try:
        cursor.execute('''SELECT * FROM bags WHERE user_id = %s''', (user_id,))
        bag_data = cursor.fetchall()
        
        if not bag_data:
            return discord.Embed(description="Your bag is empty.")

        bag = {
            'Distance Drivers': [],
            'Fairway Drivers': [],
            'Mid-Ranges': [],
            'Putt/Approach': []
        }

        for disc in bag_data:
            stability = disc[6] + disc[7]
            speed = disc[4]
            if stability < 0:
                category = 'Understable'
            elif stability == 0:
                category = 'Neutral'
            elif stability >= 0 and stability <= 2:
                category = 'Stable'
            else:
                category = 'Overstable'
            
            disc_info = f"{disc[1]} [{disc[2]}] - Plastic: {disc[3]}, Speed: {disc[4]}, Glide: {disc[5]}, Turn: {disc[6]}, Fade: {disc[7]} ({category})"
            if speed > 8:
                bag['Distance Drivers'].append(disc_info)
            elif speed > 5:
                bag['Fairway Drivers'].append(disc_info)
            elif speed > 4:
                bag['Mid-Ranges'].append(disc_info)
            else:
                bag['Putt/Approach'].append(disc_info)

        embed = discord.Embed(title=f"{ctx.author.display_name}'s Bag - Detailed")
        embed.set_thumbnail(url=ctx.author.avatar.url)  # Set thumbnail as user's profile picture

        for category, discs in bag.items():
            if discs:
                formatted_discs = "\n".join([f"{i}. {disc}" for i, disc in enumerate(discs, start=1)])
                embed.add_field(name=category, value=formatted_discs, inline=False)  # Add a field for each category

        return embed
    except Exception as e:
        return discord.Embed(description=f"An error occurred: {str(e)}")

# Command to display user's detailed bag
@bot.command(name='mybagdetailed')
async def mybagdetailed(ctx):
    try:
        user_id = ctx.author.id
        embed = format_bag_detailed(user_id, ctx)

        # Send the embedded message
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")

# Command to add a disc to the user's bag
@bot.command(name='add')
async def add(ctx, *, input_string: str):
    try:
        # Split the input string using commas as the delimiter
        parts = [part.strip() for part in input_string.split(',')]
        
        # Check if there are enough parts (name, brand, plastic, speed, glide, turn, fade)
        if len(parts) != 7:
            await ctx.send("Invalid input. Please provide disc name, brand, plastic, speed, glide, turn, and fade.")
            return
        
        # Extract the individual fields
        disc_name, brand, plastic, speed, glide, turn, fade = parts
        
        # Convert speed, glide, turn, and fade to float
        speed = float(speed)
        glide = float(glide)
        turn = float(turn)
        fade = float(fade)
        
        user_id = ctx.author.id
        print(user_id)
        print('''INSERT INTO bags VALUES (%s, %s, %s, %s, %s, %s, %s, %s)''',
                       (user_id, disc_name, brand, plastic, speed, glide, turn, fade))
        cursor.execute('''INSERT INTO bags VALUES (%s, %s, %s, %s, %s, %s, %s, %s)''',
                       (user_id, disc_name, brand, plastic, speed, glide, turn, fade))
        conn.commit()
        await ctx.send(f"Added {brand} {disc_name} to your bag.")
    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")

# Command to add multiple discs to the user's bag with a semicolon delimiter
@bot.command(name='addMultiple')
async def add_multiple(ctx, *, input_string: str):
    try:
        # Remove spaces between discs, then split using a semicolon as the delimiter
        disc_strings = input_string.split(';')

        for disc_string in disc_strings:
            # Split each disc string into individual fields
            parts = [part.strip() for part in disc_string.split(',')]

            # Check if there are enough parts (name, brand, plastic, speed, glide, turn, fade)
            if len(parts) != 7:
                await ctx.send(f"Invalid input: {disc_string}. Please provide disc name, brand, plastic, speed, glide, turn, and fade for each disc.")
                continue

            # Extract the individual fields
            disc_name, brand, plastic, speed, glide, turn, fade = parts

            # Convert speed, glide, turn, and fade to float
            speed = float(speed)
            glide = float(glide)
            turn = float(turn)
            fade = float(fade)

            user_id = ctx.author.id
            cursor.execute('''INSERT INTO bags VALUES (%s, %s, %s, %s, %s, %s, %s, %s)''',
                           (user_id, disc_name, brand, plastic, speed, glide, turn, fade))
            conn.commit()
            await ctx.send(f"Added {brand} {disc_name} to your bag.")

    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")

# Function to get a summary of the discs in the user's bag as an embedded message
def bag_summary(user_id, ctx):
    try:
        cursor.execute('''SELECT * FROM bags WHERE user_id = %s''', (user_id,))
        bag_data = cursor.fetchall()

        if not bag_data:
            return discord.Embed(description="Your bag is empty.")

        disc_types = {
            'Distance Drivers': 0,
            'Fairway Drivers': 0,
            'Mid-Ranges': 0,
            'Putt/Approach': 0
        }

        disc_categories = {
            'Understable': 0,
            'Neutral': 0,
            'Stable': 0,
            'Overstable': 0
        }

        for disc in bag_data:
            stability = disc[6] + disc[7]
            speed = disc[4]
            if speed > 8:
                type = 'Distance Drivers'
            elif speed > 5:
                type = 'Fairway Drivers'
            elif speed > 4:
                type = 'Mid-Ranges'
            else:
                type = 'Putt/Approach'
            if stability < 0:
                category = 'Understable'
            elif stability == 0:
                category = 'Neutral'
            elif stability > 0 and stability <= 2:
                category = 'Stable'
            else:
                category = 'Overstable'

            disc_types[type] += 1
            disc_categories[category] += 1

        embed = discord.Embed(title=f"{ctx.author.display_name}'s Bag Summary")

        for disc_type, count in disc_types.items():
            embed.add_field(name=disc_type, value=count, inline=True)
        for category, count in disc_categories.items():
            embed.add_field(name=category, value=count, inline=True)

        return embed

    except Exception as e:
        return discord.Embed(description=f"An error occurred: {str(e)}")

# Command to get a summary of the discs in the user's bag
@bot.command(name='bagSummary')
async def bag_summary_cmd(ctx):
    try:
        user_id = ctx.author.id
        embed = bag_summary(user_id, ctx)
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")

# Command to view someone else's bag by specifying their username
@bot.command(name='bag')
async def view_bag(ctx, username: str):
    try:
        # Find the user by username
        user = None
        for member in ctx.guild.members:
            if member.name == username:
                user = member
                break

        if not user:
            await ctx.send(f"User '{username}' not found.")
            return

        user_id = user.id
        cursor.execute('''SELECT * FROM bags WHERE user_id = %s''', (user_id,))
        bag_data = cursor.fetchall()

        if not bag_data:
            # Create an embed message for an empty bag
            embed = discord.Embed(title=f"{user.display_name}'s Bag", color=0xff0000)
            embed.set_thumbnail(url=user.avatar.url)
            embed.add_field(name="Empty Bag", value="This bag is empty.", inline=False)
            await ctx.send(embed=embed)
            return


        # Create an embed message
        embed = discord.Embed(title=f"{user.display_name}'s Bag", color=0x00ff00)

        # Set the thumbnail to the user's profile picture
        embed.set_thumbnail(url=user.avatar.url)

        # Loop through each category and add it as a field in the embed
        for category, item_count in bag_data:
            embed.add_field(name=category, value=f"Items: {item_count}", inline=False)

        # Send the embed message
        await ctx.send(embed=embed)

    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")


# Command to remove a disc from the user's bag (accepts multiple words in disc name)
@bot.command(name='removeDisc')
async def remove(ctx, *, disc_name):
    try:
        user_id = ctx.author.id
        cursor.execute('''DELETE FROM bags WHERE user_id = %s AND lower(disc_name) = %s''', (user_id, disc_name.lower()))
        conn.commit()
        await ctx.send(f"Removed {disc_name} from your bag.")

    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")

    
# Run the bot
bot.run(TOKEN)

