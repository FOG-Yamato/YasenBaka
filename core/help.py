from collections import OrderedDict
from typing import Optional

from discord import Embed
from discord.ext.commands import Group
from yaml import YAMLError, safe_load

from bot import Yasen, __title__ as name
from scripts.helpers import split_camel


def general_help(bot: Yasen, prefix: str) -> Embed:
    """
    Return a general Embed onject for help.
    :param bot: the Yasen instance.
    :param prefix: the command prefix.
    :return: a discord Embed object for general help.
    """
    description = f'For detailed help please use {prefix}help [command_name]'
    embed = Embed(colour=bot.config.colour, description=description)
    embed.set_author(name=f'{name} Help', icon_url=bot.user.avatar_url)
    cog_cmd = OrderedDict()
    for command in bot.commands:
        cog_name = ' '.join(split_camel(command.cog_name) + ['Commands'])
        if cog_name not in cog_cmd:
            cog_cmd[cog_name] = []
        cog_cmd[cog_name].append(f'`{command.name}`')
        if isinstance(command, Group):
            cog_cmd[cog_name] += [f'`{cmd.name}`' for
                                  cmd in command.all_commands.values()]
    for key, val in cog_cmd.items():
        embed.add_field(name=key, value=', '.join(val))
    return embed


def get_doc(bot: Yasen, cmd_name: Optional[str]) -> Optional[str]:
    """
    Get the doc string of a given command by name.
    :param bot: the Yasen instance.
    :param cmd_name: the name of the command.
    :return: the docstring of the command if found.
    """
    if cmd_name:
        c = bot.get_command(cmd_name)
        return c.help if c else None


def cmd_help_embed(cmd_name: str, doc: str, icon_url, prefix: str,
                   colour: int) -> Embed:
    """
    Generate help embed for a given embed.
    :param cmd_name: the command name.
    :param doc: the command doc string.
    :param icon_url: bot icon url.
    :param prefix: the prefix of the given context.
    :param colour: the colour for the embed.
    :return: the embed object for the given command.
    """
    try:
        help_dict = safe_load(doc)
    except YAMLError:
        return Embed(colour=colour, description=doc)
    else:
        embed = Embed(colour=colour, description=help_dict.pop('Description'))
        embed.set_author(name=cmd_name, icon_url=icon_url)
        for key, val in help_dict.items():
            embed.add_field(
                name=key, value=val.format(prefix=prefix), inline=False)
        return embed
