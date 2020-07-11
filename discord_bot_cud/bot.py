from random import shuffle

import discord
from discord.permissions import Permissions


# the letter(s) a valid command has to start with
START_LETTER = '.'

# the default channel name
MAIN_CHANNEL = 'Allgemein'


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
    """Singleton that stores all known commands in a dict.

    Provides decorators to easily extend existing discord
    clients with new commands.
    """
    known_commands = {}
    command_parameters = {}

    @staticmethod
    def command_list():
        txt = ''
        for cmd in DiscordCommands.known_commands.keys():
            txt += f'\n - {START_LETTER}{cmd}'
            if cmd in DiscordCommands.command_parameters:
                txt += ' ('
                txt += ', '.join(DiscordCommands.command_parameters[cmd])
                txt += ')'
        return txt

    @staticmethod
    def add_func(name, func, params=None):
        DiscordCommands.known_commands[name] = func
        if params:
            DiscordCommands.command_parameters[name] = params

    @staticmethod
    def add(args=None, *params):
        if isinstance(args, str):
            def decorator(func):
                DiscordCommands.add_func(args, func, params)
                return func
            return decorator
        else:
            name = args.__qualname__
            name = name.rsplit('.', 1)[-1]
            DiscordCommands.add_func(name, args, params)
            return args


class MyClient(discord.Client):
    """Custom discord client to """
    def __init__(self):
        super().__init__()
        # list of created channels
        self.channels = []
        # current channel we use to get member to move.
        self.main_channel = None

    async def create_channel(self, guild, nr, member):
        channel = await guild.create_voice_channel(
            f'#{nr}_gruppe')
        await member[0].move_to(channel)
        await member[1].move_to(channel)
        self.channels.append(channel)
        print(f'group {nr}: {member[0].name} - {member[1].name}')

    @DiscordCommands.add
    async def list_commands(self, msg):
        await msg.channel.send(
            'The known commands for this bot are:'+
            DiscordCommands.command_list())

    @DiscordCommands.add
    async def channel_name(self, msg):
        name = self.main_channel.name if self.main_channel else MAIN_CHANNEL
        await msg.channel.send(
            f'The channel we use for shuffeling is: "{name}"')

    @DiscordCommands.add('shuffle', 'channel_name')
    async def shuffle_pairs(self, channel_name=MAIN_CHANNEL):
        if not self.main_channel or self.main_channel.name != channel_name:
            guild, channel = self.get_voice_channel_by_name(channel_name)
            self.current_guild = guild
            self.main_channel = channel
            self.members = self.get_member_from_channel(self.main_channel)
            shuffle(self.members)
        
        # cleanup - move users and remove old channels if they exist
        self.cleanup()

        # overwrite current member list with shuffled one
        self.members = round_move(self.members)

        for idx in range(int(len(self.members)/2)):
            await self.create_channel(
                self.current_guild,
                idx + 1,
                self.members[idx * 2:idx * 2 + 2])

    def get_voice_channel_by_name(self, channel_name):
        for guild in self.guilds:
            for channel in guild.voice_channels:
                if channel.name == channel_name:
                    return guild, channel
        print(f'Error: could not find channel named {channel_name}')

    def get_member_from_channel(self, channel):
        """get all user from the channel"""
        mem = [m for m in channel.members if not m.bot and m.voice]
        print(f'Got {len(mem)} users from channel {channel.name}')
        return mem

    @DiscordCommands.add('list_channel', 'channel_name')
    async def list_channel(self, msg, channel_name):
        guild, channel = self.get_voice_channel_by_name(channel_name)
        member = self.get_member_from_channel(channel)
        txt = f'Members of channel {channel_name} are:\n - '
        txt += '\n - '.join([m.name for m in member])
        print(dir(member[0]))
        if not member:
            txt += '(the channel is empty)'
        await msg.channel.send(txt)


    @DiscordCommands.add
    async def cleanup(self):
        """Delete all known channels."""
        for channel in self.channels:
            for member in channel.members:
                member.move_to(self.main_channel)
            await channel.delete()
        self.channels = []

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
        command_and_param = txt_command[len(start):].split(' ')
        txt_command = command_and_param[0]
        txt_params = command_and_param[1:]
        commands = DiscordCommands.known_commands
        if txt_command in commands:
            if await self.author_check(msg):
                await commands[txt_command](self, msg, *txt_params)


def main(token):
    client = MyClient()
    client.run(token)
