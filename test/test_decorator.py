from discord_robot_cud.bot import DiscordCommands


def test_discord_command():
    # empty before testing
    DiscordCommands.known_commands = {}

    @DiscordCommands.add
    def foo():
        return True

    known = DiscordCommands.known_commands
    assert known == {'foo': foo}

    @DiscordCommands.add('bar')
    def blubb():
        return False

    assert known == {'foo': foo, 'bar': blubb}
