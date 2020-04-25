import os

import discord


class MyClient(discord.Client):
    async def create_channel(self, guild, nr, member):
        channel = await guild.create_voice_channel(
            f'kennenlernrunde_gruppe_#{nr}')
        print('--------------', nr)
        await member[0].move_to(channel)
        await member[1].move_to(channel)


    async def on_ready(self):
        for guild in self.guilds:
            for channel in guild.text_channels:
                if channel.name == 'Allgemein':
                    members = channel.members
                    break
            # we have the members - ignore all other guilds!
            if members:
                break

        members = [m for m in channel.members if not m.bot and m.voice]
        # TODO: resort members/get random pairing for users in members

        for i in range(int(len(members)/2)):
            await self.create_channel(guild, i+1, members[i*2:i*2+2])
            # break

        print(f'{self.user} has connected to Discord!')

    #async def on_message(self, msg):
    #    content = msg.content
    #    print(f'new message: {msg.content}')

def main(token):
    client = MyClient()
    client.run(token)
