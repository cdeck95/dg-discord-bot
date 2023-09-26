**Discord Disc Golf Bag Bot**
The Discord Disc Golf Bag Bot is a bot that allows users to manage their disc golf bag within a Discord server. Users can add, remove, and view discs in their bag, categorize them, and even view bag summaries. The bot is designed to sync data across servers and attach it to your Discord username.

**Features**

**Add Discs:** Users can add discs to their bag with details such as disc name, brand, plastic, speed, glide, turn, and fade.
**Categorization:** The bot automatically categorizes discs into four categories: Distance Drivers, Fairway Drivers, Mid-Ranges, and Putt/Approach. Users can also override the category of a disc if needed.
**View Bag:** Users can view the discs in their bag, either as a simple list or as a detailed list with disc attributes.
**Bag Summary:** Users can see a summary of their bag, including the count of discs in each category and their stability categories.
**Remove Discs:** Users can remove discs from their bag.
**Sync Across Servers:** The bot ensures that your disc bag data is accessible across different Discord servers.

**Commands**
**`!mybag`:** View your disc golf bag.
!mybagdetailed: View your disc golf bag with detailed information.
!add <disc_details>: Add a disc to your bag (e.g., !add Disc Name, Brand, Plastic, Speed, Glide, Turn, Fade).
!addMultiple <disc_details1; disc_details2; ...>: Add multiple discs to your bag at once.
!removeDisc <disc_name>: Remove a disc from your bag.
!override <disc_name>, <category>: Override the category of a disc in your bag.
!bagSummary: View a summary of your disc golf bag.
!bag <username>: View someone else's disc golf bag by specifying their username.
Setup
To invite the Discord Disc Golf Bag Bot to your server and get started, follow these steps:

Invite the Bot: Use the invite link provided to invite the bot to your server.

Configure Environment Variables: Set up environment variables for the bot's token (DISCORD_TOKEN) and any other necessary credentials (e.g., database credentials).

Run the Bot: Run the provided Python code to start the bot. Make sure you have the required Python packages installed, such as discord.py and mysql.connector.

Commands: Use the commands listed above to interact with the bot and manage your disc golf bag.

Additional Information
Syncing Data: The bot uses a MySQL database to store and sync data across servers. Ensure that the database credentials are correctly set in your environment variables.

Errors: If you encounter any issues or errors while using the bot, please contact the bot administrator for assistance.

Enjoy managing your disc golf bag with the Discord Disc Golf Bag Bot!
https://discord.com/api/oauth2/authorize?client_id=1146901955927613530&permissions=2147534912&scope=bot
