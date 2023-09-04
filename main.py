import os
import discord
from dotenv import load_dotenv
from discord.ext import commands
import requests
import sqlite3

# Credentials
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Create bot
intents = discord.Intents.all();
bot = commands.Bot(command_prefix='!', intents=intents)

# Connect to the SQLite database
conn = sqlite3.connect('bag_data.db')
cursor = conn.cursor()

# Create a table to store user bags
cursor.execute('''CREATE TABLE IF NOT EXISTS bags (
                  user_id INTEGER,
                  disc_name TEXT,
                  brand TEXT,
                  plastic TEXT,
                  speed REAL,
                  glide REAL,
                  turn REAL,
                  fade REAL
                )''')
conn.commit()

# Startup Information
@bot.event
async def on_ready():
    print('Connected to bot: {}'.format(bot.user.name))
    print('Bot ID: {}'.format(bot.user.id))

    
# Function to format and display a user's bag
def format_bag(user_id):
    try:
        cursor.execute('''SELECT * FROM bags WHERE user_id = ?''', (user_id,))
        bag_data = cursor.fetchall()
        print(bag_data)
        
        if not bag_data:
            return "Your bag is empty."

        bag = {
            'Distance Drivers': [],
            'Fairway Drivers': [],
            'Mid-Ranges': [],
            'Putt/Approach': []
        }

        for disc in bag_data:
            
            print(disc[1])
            print(disc[2])
            print(disc[3])
            print(disc[4])
            print(disc[5])
            print(disc[6])
            print(disc[7])
            stability = disc[6] + disc[7]
            print(stability)
            speed = disc[4]
            if stability < 0:
                category = 'Understable'
            elif stability == 0:
                category = 'Neutral'
            elif stability >= 0 and stability <= 2:
                category = 'Stable'
            else:
                category = 'Overstable'
            
            print(category)
            disc_info = f"{disc[1]} [{disc[2]}] - Plastic: {disc[3]}, Speed: {disc[4]}, Glide: {disc[5]}, Turn: {disc[6]}, Fade: {disc[7]} ({category})"
            if speed > 8:
                bag['Distance Drivers'].append(disc_info)
            elif speed > 5:
                bag['Fairway Drivers'].append(disc_info)
            elif speed > 4:
                bag['Mid-Ranges'].append(disc_info)
            else:
                bag['Putt/Approach'].append(disc_info)

        formatted_bag = ''
        for category, discs in bag.items():
            formatted_bag += f"**{category}**:\n\n"
            formatted_bag += '\n'.join(discs) + '\n\n'
        
        return formatted_bag
    except Exception as e:
        return f"An error occurred: {str(e)}"


# Command to display user's bag
@bot.command(name='mybag')
async def mybag(ctx):
    try:
        user_id = ctx.author.id
        bag = format_bag(user_id)
        await ctx.send(f"**{ctx.author.display_name}'s Bag**\n\n{bag}")
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
        cursor.execute('''INSERT INTO bags VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                       (user_id, disc_name, brand, plastic, speed, glide, turn, fade))
        conn.commit()
        await ctx.send(f"Added {brand} {disc_name} to your bag.")
    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")

# Command to remove a disc from the user's bag
@bot.command(name='remove')
async def remove(ctx, disc_name):
    try:
        user_id = ctx.author.id
        cursor.execute('''DELETE FROM bags WHERE user_id = ? AND lower(disc_name) = ?''', (user_id, disc_name.lower()))
        conn.commit()
        await ctx.send(f"Removed {disc_name} from your bag.")
    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")
    
# Run the bot
bot.run(TOKEN)

