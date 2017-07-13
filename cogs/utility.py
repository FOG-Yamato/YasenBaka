from discord import Embed, File, Member, User
from discord.ext import commands
from discord.ext.commands import Context

from bot import Yasen
from core.util_core import convert_currency, generate_latex_online, get_avatar


class Utility:
    """
    Class for Utility commands.
    """

    def __init__(self, bot: Yasen):
        self.bot = bot

    @commands.command()
    async def latex(self, ctx: Context, *, expression: str = None):
        """
        Description: "Compile a LaTeX erpression into an image."
        Usage: "`{prefix}latex \\\int_0^{\\\infty} \\\\frac{x}{3} dx`"
        """
        if not expression:
            await ctx.send('Please enter a valid LaTeX expression.')
            return
        res = await generate_latex_online(self.bot.session_manager, expression)
        if isinstance(res, File):
            await ctx.send(file=res)
        else:
            await ctx.send(res)

    @commands.command()
    async def avatar(self, ctx: Context, user: User = None):
        """
        Description: "Display the avatar of a user."
        Usage: |
            `{prefix}avatar some_user` for avatar of the given user.
            `{prefix}avatar` for your own avatar.
        """
        target = user or ctx.author
        embed = Embed(description=f'Avatar for {target.name}',
                      colour=self.bot.config.colour)
        embed.set_image(url=get_avatar(target))
        await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    async def joined(self, ctx: Context, member: Member = None):
        """
        Description: "Display when the member joined the guild."
        Restriction: Cannot be used in private message.
        Usage: |
            `{prefix}joined some_user` for join time of the given user.
            `{prefix}joined` for join time of yourself.
        """
        target = member or ctx.author
        time = target.joined_at.strftime('%Y-%m-%d')
        await ctx.send(f'{target} joined at {time}')

    @commands.command()
    async def currency(self, ctx: Context, from_: str = None,
                       to: str = None, amount: str = '1'):
        """
        Description: Currency conversion.
        Usage: |
            `{prefix} FROM TO [AMOUNT]` if amount is not provided it defaults to 1.
            `{prefix} CAD USD 12` to convert 12 Canadian dollars to US dollars.
            `{prefix} EUR JPY` to convert 1 Euro to Japanese Yen.
        """
        if not from_ or not to:
            await ctx.send('Please enter vaild currency codes '
                           'for the base currency and the target currency.')
            return
        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError
        except ValueError:
            await ctx.send('Please enter a number greater '
                           'than 0 for the amount.')
            return
        await ctx.send(
            await convert_currency(
                self.bot.session_manager, self.bot.config.currency,
                from_, to, amount
            )
        )
