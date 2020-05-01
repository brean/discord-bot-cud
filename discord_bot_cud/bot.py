from random import shuffle

import discord
from discord.permissions import Permissions

# the letter(s) a valid command has to start with
START_LETTER = '.'

# the default channel name
MAIN_CHANNEL_NAME = 'Allgemein'


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
    """Stores all known commands in a dict.

    Provides decorators to easily extend existing discord
    clients with new commands.
    """
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
    """Custom discord client to """
    def __init__(self):
        super().__init__()
        # list of created channels
        self.channels = []
        # list of moved users
        self.moved_user = []

    async def create_channel(self, guild, nr, member):
        channel = await guild.create_voice_channel(
            f'#{nr}_gruppe')
        await member[0].move_to(channel)
        await member[1].move_to(channel)
        self.channels.append(channel)
        self.moved_member += member
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

    def get_member_from_channel(self, channel_name=MAIN_CHANNEL_NAME):
        """get all user from the channel"""
        self.main_channel = None
        for guild in self.guilds:
            for channel in guild.voice_channels:
                if channel.name == channel_name:
                    self.current_guild = guild
                    self.main_channel = channel
                    mem = channel.members
                    mem = [m for m in mem if not m.bot and m.voice]
                    shuffle(mem)
                    return mem
        if not self.main_channel:
            print(f'Error: could not find channel named {channel_name}')

    @DiscordCommands.add
    async def cleanup(self):
        """Delete all known channels."""
        if self.main_channel:
            for member in self.moved_member:
                member.move_to(self.main_channel)
        for channel in self.channels:
            await channel.delete()
        self.channels = []
        self.moved_member = []

    async def create_role_and_assign_user(self, role_name="testrolle"):
        guild = self.main_channel.guild
        roles = [r for r in guild.roles if r.name == role_name]
        if len(roles) == 0:
            roles = [await guild.create_role(name=role_name)]
        for mem in self.members:
            for role in roles:
                await mem.add_roles(role)

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
                await commands[txt_command](self)


def main(token):
    client = MyClient()
    client.run(token)
