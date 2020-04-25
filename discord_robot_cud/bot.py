from random import shuffle
import os

import discord


class MyClient(discord.Client):
    async def create_channel(self, guild, nr, member):
        channel = await guild.create_voice_channel(
            f'#{nr}_kennlerngruppe')
        await member[0].move_to(channel)
        await member[1].move_to(channel)
        self.channels.append(channel)
        print(f'group {nr}: {member[0].name} - {member[1].name}')

    async def shuffle_pairs(self):
        nr = 0
        guild = self.current_guild
        # get copy of members
        members = []+self.members
        while len(members) >= 2:
            shuffle(members)
            m1, m2 = members[:2]
            if m2.id in self.member_pairings[m1.id]:
                continue
                # we already had this paring!
                # this might end in an endless loop but -.-
            else:
                del members[members.index(m1)]
                del members[members.index(m2)]
                self.member_pairings[m1.id].append(m2.id)
                self.member_pairings[m2.id].append(m1.id)
                nr += 1
                await self.create_channel(guild, nr, [m1, m2])

    def get_member_from_channel(self):
        for guild in self.guilds:
            for channel in guild.text_channels:
                if channel.name == 'Allgemein':
                    self.current_guild = guild
                    mem = channel.members
                    return [m for m in mem if not m.bot and m.voice]

    async def on_ready(self):
        self.channels = []
        self.members = self.get_member_from_channel()

        self.member_pairings = {}
        for m in member:
            self.member_pairings[m.id] = []

        print(f'{self.user} has connected to Discord!')

    async def cleanup(self):
        for channel in self.channels:
            await channel.remove()

    async def on_message(self, msg):
        content = msg.content
        if content == 'bot_shuffle':
            await self.shuffle_pairs()
        if content == 'bot_cleanup':
            await self.cleanup()


def main(token):
    client = MyClient()
    client.run(token)
