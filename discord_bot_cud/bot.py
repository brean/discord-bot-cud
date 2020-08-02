import asyncio
from random import shuffle
import pathlib
import yaml

import discord
from discord.permissions import Permissions


# the letter(s) a valid command has to start with
START_LETTER = '.'

# the default channel name
MAIN_CHANNEL = 'Allgemein'

# time in seconds when we shuffle again, set to <=0 for manual shuffeling
SHUFFLE_TIME = 5 * 60

# time in seconds we show how much time is remaining in the main channel
INFO_TIME = 60


default_lang = 'de'

CHANNEL_SUFFIX = '_gruppe'

translations = {}

with open(pathlib.Path().absolute() / 'data' / 'translations.yml') as yaml_file:
    translations = yaml.full_load(yaml_file)


def translate(txt, lang=None):
    global translations, default_lang
    if not lang:
        lang = default_lang
    if txt in translations[default_lang]:
        tra = translations[default_lang][txt]
        if isinstance(tra, list):
            return rnd.choice(tra)
        else:
            return tra
    else:
        print(f'not translated: {txt}')
        return f'TRANSLATE_{txt}'


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


def format_time(sec):
    return f'{int(sec/60)}:{sec%60:02d}'


class DiscordCommands:
    """Singleton that stores all known commands in a dict.

    Provides decorators to easily extend existing discord
    clients with new commands.
    """
    known_commands = {}
    command_parameters = {}

    @staticmethod
    def command_list():
        """Return command list as text."""
        txt = ''
        for cmd in DiscordCommands.known_commands.keys():
            txt += f'\n - {START_LETTER}{cmd}'
            if cmd in DiscordCommands.command_parameters:
                cmds = ', '.join(DiscordCommands.command_parameters[cmd])
                txt += f' ({cmds})'
        return txt

    @staticmethod
    def _add_func(name, func, params=None):
        DiscordCommands.known_commands[name] = func
        if params:
            DiscordCommands.command_parameters[name] = params

    @staticmethod
    def add(args=None, *params):
        if isinstance(args, str):
            def decorator(func):
                DiscordCommands._add_func(args, func, params)
                return func
            return decorator
        else:
            name = args.__qualname__.rsplit('.', 1)[-1]
            DiscordCommands._add_func(name, args, params)
            return args


def member_name(member):
    """Small helper to show user name and nick."""
    if member.nick:
        return f'{member.name} ({member.nick})'
    else:
        return member.name

async def try_to_move_channel(member, channel):
    try:
        await member.move_to(channel)
    except discord.errors.HTTPException:
        print(translate('cannot_move_user').format(member_name(member), channel.name))
        await member.send(translate('can_not_move_you').format(channel.name))

def get_channel_by_name(guilds, channel_name):
    for guild in guilds:
        for channel in guild.voice_channels:
            if channel.name == channel_name:
                return guild, channel
        for channel in guild.text_channels:
            if channel.name == channel_name:
                return guild, channel
    print(translate('channel_not_found').format(channel_name))
    return None, None


def get_voice_channel_by_name(guilds, channel_name):
    for guild in guilds:
        for channel in guild.voice_channels:
            if channel.name == channel_name:
                return guild, channel
    print(translate('channel_not_found').format(channel_name))
    return None, None


def get_member_from_channel(channel):
    """get all user from the channel"""
    mem = [m for m in channel.members if not m.bot and m.voice]
    print(translate('mem_in_chan').format(len(mem), channel.name))
    return mem


class MyClient(discord.Client):
    """Custom discord client to """
    def __init__(self):
        super().__init__()
        # list of created channels
        self.channels = []
        # current channel we use to get member to move.
        self.main_channel = None
        # time in seconds we reshuffle
        self.shuffle_time = SHUFFLE_TIME
        self.shuffle_timer = None

    async def create_channel(self, guild, nr, member):
        try:
            name = f'#{nr}{CHANNEL_SUFFIX}'
            channel = await guild.create_voice_channel(name)
            await try_to_move_channel(member[0], channel)
            await try_to_move_channel(member[1], channel)
            self.channels.append(channel)
            print(f'{name}: {member[0].name} - {member[1].name}')
        except Exception:
            pass

    @DiscordCommands.add
    async def list_commands(self, msg):
        await msg.channel.send(
            translate('known_commands') +
            DiscordCommands.command_list())

    @DiscordCommands.add
    async def channel_name(self, msg):
        name = self.main_channel.name if self.main_channel else MAIN_CHANNEL
        await msg.channel.send(
            translate('shuffle_channel').format(name))

    @DiscordCommands.add('language', 'language')
    async def switch_language(self, msg, language=None):
        global default_lang
        if language in translations and language != default_lang:
            await msg.channel.send(translate('switch_from'))
            default_lang = language
            await msg.channel.send(translate('switch_to'))

    @DiscordCommands.add('list_channel', 'channel_name')
    async def list_channel(self, msg, channel_name=None):
        if channel_name:
            guild, channel = get_voice_channel_by_name(
                self.guilds, channel_name)
        elif self.main_channel:
            channel = self.main_channel
        else:
            await msg.channel.send(translate('no_channel_name'))
            return
        if not channel:
            await msg.channel.send(
                translate('voice_channel_not_found').format(channel_name))
            return
        member = get_member_from_channel(channel)
        txt = translate('members').format(channel.name) + '\n - '
        txt += '\n - '.join([m.name for m in member])
        if not member:
            txt += translate('empty')
        await msg.channel.send(txt)

    @DiscordCommands.add('simulate_shuffle', 'channel_name')
    async def sim_shuffle_pairs(self, msg, channel_name=MAIN_CHANNEL):
        if not self.main_channel or self.main_channel.name != channel_name:
            guild, channel = get_channel_by_name(self.guilds, channel_name)
            self.current_guild = guild
            self.main_channel = channel
            self.members = self.main_channel.members
            shuffle(self.members)
            await self.make_even(msg)

        # no need to clean up

        # everyone moves one position in list
        self.members = round_move(self.members)

        # simulate channel creation
        txt = translate('shuffle_user')+':\n'
        for idx in range(int(len(self.members)/2)):
            nr = idx+1
            member = self.members[idx * 2:idx * 2 + 2]
            name = f'#{nr}{CHANNEL_SUFFIX}'
            txt += f'{name}: {member[0].name} - {member[1].name}\n'
        await msg.channel.send(txt)

        if self.shuffle_time > 0:
            self.current_shuffle = self.shuffle_time
            if not self.shuffle_timer:
                self.shuffle_timer = self.loop.create_task(
                    self.reshuffle(msg, self.sim_shuffle_pairs))

    @DiscordCommands.add('shuffle_time', 'time_in_seconds')
    async def show_edit_shuffle_time(self, msg, time_in_seconds=-2):
        try:
            if isinstance(time_in_seconds, str):
                if ':' in time_in_seconds:
                    if len(time_in_seconds.split(':')) > 2:
                        return
                    minutes, seconds = [
                        int(i) for i in time_in_seconds.split(':')]
                    time_in_seconds = minutes * 60 + seconds
            if int(time_in_seconds) > -2:
                self.shuffle_time = int(time_in_seconds)
            t = format_time(self.shuffle_time)
            await msg.channel.send(translate('shuffle_time').format(t))
        except ValueError:
            await msg.channel.send(
                translate('not_time').format(time_in_seconds))

    async def make_even(self, msg):
        if len(self.members) % 2 == 1:
            txt = translate('not_even').format(self.members[-1].name)
            await msg.channel.send(txt)
            self.members = self.members[:-1]

    @DiscordCommands.add('shuffle', 'channel_name')
    async def shuffle_pairs(self, msg, channel_name=MAIN_CHANNEL):
        if not self.main_channel or self.main_channel.name != channel_name:
            guild, channel = get_voice_channel_by_name(
                self.guilds, channel_name)
            self.current_guild = guild
            self.main_channel = channel
            self.members = get_member_from_channel(self.main_channel)
            shuffle(self.members)
            await self.make_even(msg)

        # cleanup - move users and remove old channels if they exist
        self.cleanup()

        # everyone moves one position in list
        self.members = round_move(self.members)

        for idx in range(int(len(self.members)/2)):
            await self.create_channel(
                self.current_guild,
                idx + 1,
                self.members[idx * 2:idx * 2 + 2])

        # lets do it again in a few seconds!
        if self.shuffle_time > 0:
            self.current_shuffle = self.shuffle_time
            if not self.shuffle_timer:
                self.shuffle_timer = self.loop.create_task(
                    self.reshuffle(msg, self.shuffle_pairs))

    @DiscordCommands.add
    async def stop_shuffle(self, msg):
        if self.shuffle_timer:
            await msg.channel.send(translate('shuffle_stopped'))
            self.shuffle_timer.cancel()
            self.shuffle_timer = None
        else:
            await msg.channel.send(translate('no_shuffle'))

    @DiscordCommands.add
    async def cleanup(self):
        """Delete all known channels."""
        for channel in self.channels:
            for member in channel.members:
                await try_to_move_channel(member, self.main_channel)
            await channel.delete()
        self.channels = []

    async def reshuffle(self, msg, shuffle_func):
        while True:
            while self.current_shuffle > INFO_TIME:
                self.current_shuffle -= INFO_TIME
                await asyncio.sleep(INFO_TIME)
                time = format_time(self.current_shuffle)
                await msg.channel.send(f'{time} left!')
            await asyncio.sleep(self.current_shuffle)
            self.current_shuffle = 0
            await shuffle_func(msg, channel_name=self.main_channel.name)

    async def on_ready(self):
        """Discord client is ready, set member of channel"""
        print(translate('ready').format(self.user.name))

    async def author_check(self, msg):
        guild_perm = msg.author.guild_permissions
        if guild_perm != Permissions.all():
            name = member_name(msg.author)
            await msg.channel.send(translate('not_admin').format(msg.author))
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
                func = commands[txt_command] 
                await func(self, msg, *txt_params)


def main(token):
    client = MyClient()
    client.run(token)
