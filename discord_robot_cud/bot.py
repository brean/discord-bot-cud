from random import shuffle

import discord
from discord.permissions import Permissions

# the letter(s) a valid command has to start with
START_LETTER = '.'


def round_move(lst: list):
    """simple algorithm to move to next one inside of groups."""
    new = ['x'] * len(lst)
    new[1] = lst[0]
    new[len(lst)-2] = lst[len(lst)-1]
    for idx in range(1, len(lst)-1):
        if idx % 2 == 0:
            new[idx-2] = lst[idx]
        else:
            new[idx+2] = lst[idx]
    return new


class DiscordCommands:
    known_commands = {}

    @staticmethod
    def add_func(name, func):
        DiscordCommands.known_commands[name] = func

    @staticmethod
    def add(args=None):
        if isinstance(args, str):
            def decorator(func):
                DiscordCommands.add_func(args, func)
                return func
            return decorator
        else:
            name = args.__qualname__
            name = name.rsplit('.', 1)[-1]
            DiscordCommands.add_func(name, args)
            return args


class MyClient(discord.Client):
    async def create_channel(self, guild, nr, member):
        channel = await guild.create_voice_channel(
            f'#{nr}_gruppe')
        await member[0].move_to(channel)
        await member[1].move_to(channel)
        self.channels.append(channel)
        print(f'group {nr}: {member[0].name} - {member[1].name}')

    @DiscordCommands.add('shuffle')
    async def shuffle_pairs(self):
        guild = self.current_guild
        self.members = round_move(self.members)
        for idx in range(int(len(self.members)/2)):
            await self.create_channel(
                guild,
                idx + 1,
                self.members[idx * 2:idx * 2 + 2])

    def get_member_from_channel(self):
        """get all user from the channel"""
        for guild in self.guilds:
            for channel in guild.text_channels:
                if channel.name == 'Allgemein':
                    self.current_guild = guild
                    mem = channel.members
                    mem = [m for m in mem if not m.bot and m.voice]
                    shuffle(mem)
                    return mem

    @DiscordCommands.add
    async def cleanup(self):
        """Delete all known channels."""
        for channel in self.channels:
            await channel.remove()

    async def on_ready(self):
        """Discord client is ready, set member of channel"""
        self.members = self.get_member_from_channel()
        print(f'{self.user} has connected to Discord!')

    async def author_check(self, msg):
        guild_perm = msg.author.guild_permissions
        if guild_perm != Permissions.all():
            await msg.channel.send(f'Sorry, {msg.author}, you are not Admin!')
            return False
        return True

    async def on_message(self, msg):
        txt_command = msg.content
        start = START_LETTER
        if not txt_command.startswith(start):
            return
        txt_command = txt_command[len(start):]
        commands = DiscordCommands.known_commands
        if txt_command in commands:
            if await self.author_check(msg):
                await commands[txt_command]()


def main(token):
    client = MyClient()
    client.run(token)
