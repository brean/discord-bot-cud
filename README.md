# discord bot for code+design

Discord bot that creates groups of 2 for Online [Code+Design](http://code.design) Camps

[![Build Status](https://api.travis-ci.com/brean/discord-bot-cud.svg)](https://travis-ci.com/brean/discord-bot-cud)

## Installation and usage

1. create the bot in the discrod developer portal: https://discordapp.com/developers/applications.
1. add an .env file with the following content: `DISCORD_TOKEN='YOUR_DISCORD_TOKEN'`.
1. add the bot to your discord channel in discord.

Feel free to use for sudden speed dating needs.

## Known commands:
 - **.list_commands** 
   - List all commands of the bot
 - **.channel_name**
    - shows the channel name of the main channel
 - **.list_channel (channel_name)**
    - list all member of a given channel (that have voice and are not bots)
 - **.simulate_shuffle (channel_name)**
    - simulate a shuffle for a given channel (only messages the users and groups, does not create any rooms or move any member)
 - **.shuffle_time (time_in_seconds)**
    - set the time after the users are moved to the next spot (starts at 5 minutes)
 - **.shuffle (channel_name)**
    - starts a shuffle on a given channel name (that have voice and are not bots)
 - **.stop_shuffle**
    - Stops the reshuffeling (You might want to call cleanup afterwards to delete all rooms or run shuffle again for a second run)
 - **.cleanup**
    - Delete all channels created by the bot and move all user back to the main channel
