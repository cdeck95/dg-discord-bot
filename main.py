import os
import discord
from dotenv import load_dotenv
from discord.ext import commands
import requests
import mysql.connector
import mysql.connector.pooling
import asyncio
import threading
import time

# Credentials
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
USER = os.getenv('RDS_USER')
PASS = os.getenv('RDS_PASSWORD')
HOST = os.getenv('RDS_HOST')

# Create bot
intents = discord.Intents.all();
bot = commands.Bot(command_prefix='!', intents=intents, case_insensitive=True)

# Create a function to create a MySQL connection
def create_mysql_connection():
    try:
        connection = mysql.connector.connect(
            host=HOST,
            user=USER,
            password=PASS,
            database='discgolfdb'
        )
        return connection
    except mysql.connector.Error as err:
        print(f"Error creating MySQL connection: {err}")
        return None

# Initialize the MySQL connection
conn = create_mysql_connection()
cursor = conn.cursor()

# Function to execute MySQL queries with retries
def execute_mysql_query(query, *args):
    global conn  # Declare conn as a global variable
    global cursor  # Declare cursor as a global variable
    max_retries = 3
    retries = 0
    while retries < max_retries:
        try:
            if conn.is_connected():
                cursor.execute(query, args)
                conn.commit()
                return  # Remove cursor.close() from here
            else:
                # Reconnect if the connection is lost
                print("Reconnecting to MySQL...")
                conn = create_mysql_connection()
                cursor = conn.cursor()
        except mysql.connector.Error as err:
            print(f"Error executing MySQL query: {err}")
            retries += 1
    print(f"Max retries reached for query: {query}")
    raise Exception("Failed to execute MySQL query after max retries")


# Function to execute MySQL queries with retries for SELECT queries
def execute_select_query(query, *args):
    global conn  # Declare conn as a global variable
    global cursor  # Declare cursor as a global variable
    max_retries = 3
    retries = 0
    while retries < max_retries:
        try:
            if conn.is_connected():
                if cursor is None:
                    cursor = conn.cursor()  # Create a cursor if it doesn't exist
                cursor.execute(query, args)
                results = cursor.fetchall()  # Fetch the results
                conn.commit()
                return results
            else:
                # Reconnect if the connection is lost
                print("Reconnecting to MySQL...")
                conn = create_mysql_connection()
                cursor = conn.cursor()
        except mysql.connector.Error as err:
            print(f"Error executing MySQL query: {err}")
            retries += 1
    print(f"Max retries reached for query: {query}")
    raise Exception("Failed to execute MySQL query after max retries")


# Startup Information
@bot.event
async def on_ready():
    print('Connected to bot: {}'.format(bot.user.name))
    print('Bot ID: {}'.format(bot.user.id))




# Function to format and display a user's bag as an embedded message
def format_bag(user_id, ctx):
    try:
        query = '''SELECT * FROM bags WHERE user_id = %s'''
        result = execute_select_query(query, user_id)
        
        if not result:
            return discord.Embed(description="Your bag is empty.")

        bag = {
            'Distance Drivers': [],
            'Fairway Drivers': [],
            'Mid-Ranges': [],
            'Putt/Approach': []
        }

        # Sort the bag_data by speed in descending order (highest speed first)
        result.sort(key=lambda x: x[4], reverse=True)

        for disc in result:
            speed = disc[4]
            override_category = disc[8]
            if override_category:
                category = override_category
                if category == 'Distance Drivers':
                    bag['Distance Drivers'].append(disc[1])  # Add disc name to the category
                elif category == 'Fairway Drivers':
                    bag['Fairway Drivers'].append(disc[1])
                elif category == 'Mid-Ranges':
                    bag['Mid-Ranges'].append(disc[1])
                else:
                    bag['Putt/Approach'].append(disc[1])
            else:
                if speed > 8:
                    bag['Distance Drivers'].append(disc[1])  # Add disc name to the category
                elif speed > 5:
                    bag['Fairway Drivers'].append(disc[1])
                elif speed > 4:
                    bag['Mid-Ranges'].append(disc[1])
                else:
                    bag['Putt/Approach'].append(disc[1])

        embed = discord.Embed(title=f"{ctx.author.display_name}'s Bag")
        # Check if the user has a profile picture and set the thumbnail accordingly
        if ctx.author.avatar:
            embed.set_thumbnail(url=ctx.author.avatar.url)
        else:
            # If the user doesn't have a profile picture, you can set it to a default image or the bot's avatar
            embed.set_thumbnail(url=bot.user.avatar.url)

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
        await ctx.send(f"An error occurred in my bag: {str(e)}")



# Function to format and display a user's bag with details in an embedded message
def format_bag_detailed(user_id, ctx):
    try:
        query = '''SELECT * FROM bags WHERE user_id = %s'''
        result = execute_select_query(query, user_id)

        if not result:
            return discord.Embed(description="Your bag is empty.")

        bag = {
            'Distance Drivers': [],
            'Fairway Drivers': [],
            'Mid-Ranges': [],
            'Putt/Approach': []
        }

        # Sort the bag_data by speed in descending order (highest speed first)
        result.sort(key=lambda x: x[4], reverse=True)

        for disc in result:
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
            
            override_category = disc[8]
            if override_category:
                category = override_category
                if category == 'Distance Drivers':
                    bag['Distance Drivers'].append(disc_info)
                elif category == 'Fairway Drivers':
                    bag['Fairway Drivers'].append(disc_info)
                elif category == 'Mid-Ranges':
                    bag['Mid-Ranges'].append(disc_info)
                else:
                    bag['Putt/Approach'].append(disc_info)
            else:
                if speed > 8:
                    bag['Distance Drivers'].append(disc_info)
                elif speed > 5:
                    bag['Fairway Drivers'].append(disc_info)
                elif speed > 4:
                    bag['Mid-Ranges'].append(disc_info)
                else:
                    bag['Putt/Approach'].append(disc_info)

        embed = discord.Embed(title=f"{ctx.author.display_name}'s Bag - Detailed")
        if ctx.author.avatar:
            embed.set_thumbnail(url=ctx.author.avatar.url)
        for category, discs in bag.items():
            if discs:
                # Initialize the field value as an empty string
                field_value = ""
                for i, disc in enumerate(discs, start=1):
                    # Check if adding the next disc would exceed the character limit
                    if len(field_value) + len(f"{i}. {disc}\n") > 1024:
                        # If it does, break and add the field to the embed
                        embed.add_field(name=category, value=field_value, inline=False)
                        field_value = ""

                    # Add the disc info to the field value
                    field_value += f"{i}. {disc}\n"

                # Add any remaining discs as a field
                if field_value:
                    embed.add_field(name=category, value=field_value, inline=False)

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

# Command to override the category of a disc in the user's bag
@bot.command(name='override')
async def override(ctx, *, args):
    try:
        # Split the arguments using a comma as the separator
        arguments = [arg.strip() for arg in args.split(',')]

        # Check if there are enough arguments
        if len(arguments) < 2:
            embed = discord.Embed(
                title="Invalid Input",
                description="Please provide at least 2 arguments: disc_name, overridden_category.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        # Extract the arguments
        disc_name = arguments[0]
        overridden_category = arguments[1]

        valid_categories = ['Distance Drivers', 'Fairway Drivers', 'Mid-Ranges', 'Putt/Approach']


        # Join the remaining arguments (if any) as a single string
        other_args = ", ".join(arguments[2:])

        user_id = ctx.author.id
        if overridden_category == 'Distance Drivers' or overridden_category == 'Fairway Drivers' or overridden_category == 'Mid-Ranges' or overridden_category == 'Putt/Approach':
            query = '''UPDATE bags SET overridden_category = %s WHERE user_id = %s AND lower(disc_name) = %s'''
            execute_mysql_query(query, overridden_category, user_id, disc_name.lower())
            embed = discord.Embed(
                title="Category Overridden",
                description=f"Overridden category for {disc_name} is now: {overridden_category}",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="Invalid Category",
                description=f"Invalid category: {overridden_category}. Please use one of {', '.join(valid_categories)}.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    except Exception as e:
        embed = discord.Embed(
            title="Error",
            description=f"An error occurred: {str(e)}",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

@bot.command(name='overrideMultiple')
async def override_multiple(ctx, *, args):
    try:
        # Split the arguments using a comma as the separator
        arguments = [arg.strip() for arg in args.split(',')]

        # Check if there are enough arguments
        if len(arguments) % 2 != 0:
            embed = discord.Embed(title="Update Multiple Disc Categories", color=discord.Color.red())
            embed.add_field(name="Error", value="Invalid input. Please provide pairs of disc_name and new_category separated by commas.")
            await ctx.send(embed=embed)
            return

        # Initialize lists to store disc_name and new_category pairs
        disc_name_list = []
        new_category_list = []

        # Define valid categories
        valid_categories = ['Distance Drivers', 'Fairway Drivers', 'Mid-Ranges', 'Putt/Approach']

        # Extract disc_name and new_category pairs
        for i in range(0, len(arguments), 2):
            disc_name_list.append(arguments[i])
            new_category = arguments[i + 1]

            # Check if the new_category is valid
            if new_category not in valid_categories:
                embed = discord.Embed(title="Update Multiple Disc Categories", color=discord.Color.red())
                embed.add_field(name="Error", value=f"Invalid category: {new_category}. Please use one of {', '.join(valid_categories)}.")
                await ctx.send(embed=embed)
                return

            new_category_list.append(new_category)

        # Update the categories in the database
        user_id = ctx.author.id
        query = '''UPDATE bags SET overridden_category = %s WHERE user_id = %s AND LOWER(disc_name) = LOWER(%s)'''
        for disc_name, new_category in zip(disc_name_list, new_category_list):
            execute_mysql_query(query, new_category, user_id, disc_name)

        embed = discord.Embed(title="Update Multiple Disc Categories", color=discord.Color.green())
        embed.add_field(name="Success", value="Categories updated successfully.")
        await ctx.send(embed=embed)
    except Exception as e:
        embed = discord.Embed(title="Update Multiple Disc Categories", color=discord.Color.red())
        embed.add_field(name="Error", value=f"An error occurred: {str(e)}")
        await ctx.send(embed=embed)


# Command to add a disc to the user's bag
@bot.command(name='add')
async def add(ctx, *, input_string: str, overridden_category: str = None):
    try:
        # Split the input string using commas as the delimiter
        parts = [part.strip() for part in input_string.split(',')]
        
        # Check if there are enough parts (name, brand, plastic, speed, glide, turn, fade)
        if len(parts) != 7:
            embed = discord.Embed(
                title="Invalid Input",
                description="Please provide disc name, brand, plastic, speed, glide, turn, and fade.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Extract the individual fields
        disc_name, brand, plastic, speed, glide, turn, fade = parts
        
        # Convert speed, glide, turn, and fade to float
        speed = float(speed)
        glide = float(glide)
        turn = float(turn)
        fade = float(fade)
        
        user_id = ctx.author.id
        query = '''INSERT INTO bags VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)'''
        execute_mysql_query(query, user_id, disc_name, brand, plastic, speed, glide, turn, fade, overridden_category)

        if overridden_category:
            embed = discord.Embed(
                            title="Disc Added",
                            description=f"Added {brand} {disc_name} to your bag with overridden category: {overridden_category}",
                            color=discord.Color.green()
                        )        
        else:
            embed = discord.Embed(
                    title="Disc Added",
                    description=f"Added {brand} {disc_name} to your bag.",
                    color=discord.Color.green()
                )
        await ctx.send(embed=embed)
    except Exception as e:
        embed = discord.Embed(
            title="Error",
            description=f"An error occurred: {str(e)}",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

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
            query = '''INSERT INTO bags VALUES (%s, %s, %s, %s, %s, %s, %s, %s)'''
            execute_mysql_query(query, user_id, disc_name, brand, plastic, speed, glide, turn, fade)
            await ctx.send(f"Added {brand} {disc_name} to your bag.")

    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")



# Function to get a summary of the discs in the user's bag as an embedded message
def bag_summary(user_id, ctx):
    try:
        query = '''SELECT * FROM bags WHERE user_id = %s'''
        # bag_data = execute_select_query(query, (user_id,))
        bag_data = execute_select_query(query, user_id)


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

        manufacturer_count = {}  # Dictionary to store manufacturer counts

        for disc in bag_data:
            stability = disc[6] + disc[7]
            speed = disc[4]
            manufacturer = disc[2]  
            override_category = disc[8]
            if override_category:
                type = override_category
            else:
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

            # Count manufacturers
            if manufacturer in manufacturer_count:
                manufacturer_count[manufacturer] += 1
            else:
                manufacturer_count[manufacturer] = 1

        embed = discord.Embed(title=f"{ctx.author.display_name}'s Bag Summary")

        for disc_type, count in disc_types.items():
            embed.add_field(name=disc_type, value=count, inline=True)
        for category, count in disc_categories.items():
            embed.add_field(name=category, value=count, inline=True)

        # Add manufacturer counts to the embed
        for manufacturer, count in manufacturer_count.items():
            embed.add_field(name=manufacturer, value=count, inline=True)

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
        query = '''SELECT * FROM bags WHERE user_id = %s'''
        result = execute_select_query(query, user_id)

        if not result:
            # Create an embed message for an empty bag
            embed = discord.Embed(title=f"{user.display_name}'s Bag", color=0xff0000)
            # Check if the user has a profile picture and set the thumbnail accordingly
            if user.avatar:
                print("has avatar")
                embed.set_thumbnail(url=user.avatar)
            else:
                print("does not have avatar")
                # If the user doesn't have a profile picture, you can set it to a default image or the bot's avatar
                embed.set_thumbnail(url=ctx.bot.user.avatar.url)
            embed.add_field(name="Empty Bag", value="This bag is empty.", inline=False)
            await ctx.send(embed=embed)
            return

        # Sort the bag_data by speed in descending order (highest speed first)
        result.sort(key=lambda x: x[4], reverse=True)

        bag = {
            'Distance Drivers': [],
            'Fairway Drivers': [],
            'Mid-Ranges': [],
            'Putt/Approach': []
        }

        for disc in result:
            speed = disc[4]
            override_category = disc[8]
            if override_category:
                category = override_category
                if category == 'Distance Drivers':
                    bag['Distance Drivers'].append(disc[1])  # Add disc name to the category
                elif category == 'Fairway Drivers':
                    bag['Fairway Drivers'].append(disc[1])
                elif category == 'Mid-Ranges':
                    bag['Mid-Ranges'].append(disc[1])
                else:
                    bag['Putt/Approach'].append(disc[1])
            else:
                if speed > 8:
                    bag['Distance Drivers'].append(disc[1])  # Add disc name to the category
                elif speed > 5:
                    bag['Fairway Drivers'].append(disc[1])
                elif speed > 4:
                    bag['Mid-Ranges'].append(disc[1])
                else:
                    bag['Putt/Approach'].append(disc[1])

        embed = discord.Embed(title=f"{user.display_name}'s Bag")
        if user.avatar:
            print("has avatar")
            embed.set_thumbnail(url=user.avatar)
        else:
            print("does not have avatar")
            # If the user doesn't have a profile picture, you can set it to a default image or the bot's avatar
            embed.set_thumbnail(url=ctx.bot.user.avatar.url)

        for category, discs in bag.items():
            if discs:
                embed.add_field(name=category, value=', '.join(discs), inline=False)  # Add a field for each category

        await ctx.send(embed=embed)

    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")

# Function to execute DELETE MySQL queries with retries
def execute_delete_query(query, *args):
    global conn
    global cursor
    max_retries = 3
    retries = 0
    while retries < max_retries:
        try:
            if conn.is_connected():
                cursor.execute(query, args)
                conn.commit()
                # cursor.close()  # Close the cursor after executing the query
                return
            else:
                # Reconnect if the connection is lost
                print("Reconnecting to MySQL...")
                conn = create_mysql_connection()
                cursor = conn.cursor()
        except mysql.connector.Error as err:
            print(f"Error executing MySQL query: {err}")
            retries += 1
    print(f"Max retries reached for query: {query}")
    raise Exception("Failed to execute MySQL query after max retries")


# Command to remove a disc from the user's bag (accepts multiple words in disc name)
@bot.command(name='removeDisc')
async def remove(ctx, disc_name, *, countToRemove=None):
    try:
        user_id = ctx.author.id
        # Remove any commas from disc_name
        disc_name = disc_name.replace(',', '')
        query = '''DELETE FROM bags WHERE user_id = %s AND lower(disc_name) = %s'''
        
        if countToRemove is not None:
            countToRemove = int(countToRemove)  # Ensure countToRemove is an integer
            if countToRemove == 1:
                query += ' LIMIT 1'
                execute_delete_query(query, user_id, disc_name.lower())
                embed = discord.Embed(
                    title="Disc Removed",
                    description=f"Removed the first occurrence of {disc_name} from your bag.",
                    color=discord.Color.green()
                )
            else:
                query += ' LIMIT %s'
                execute_delete_query(query, user_id, disc_name.lower(), countToRemove)
                embed = discord.Embed(
                    title="Disc Removed",
                    description=f"Removed the first {countToRemove} occurrences of {disc_name} from your bag.",
                    color=discord.Color.green()
                )
        else:
            execute_delete_query(query, user_id, disc_name.lower())  # Remove LIMIT if countToRemove is not specified
            embed = discord.Embed(
                title="Disc Removed",
                description=f"Removed all occurrences of {disc_name} from your bag.",
                color=discord.Color.green()
            )
        
        await ctx.send(embed=embed)
    except Exception as e:
        embed = discord.Embed(
            title="Error",
            description=f"An error occurred: {str(e)}",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

    
# Run the bot
bot.run(TOKEN)