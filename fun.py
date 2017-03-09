"""Commands for fun"""
from discord.ext import commands
import random
from os.path import join
from helpers import read_kana_files, freadlines, fopen_generic


class Fun:
    """Commands for fun"""

    def __init__(self, bot):
        self.kanna_files = read_kana_files()
        self.bot = bot
        self.lewds = freadlines(fopen_generic(join('data', 'lewd')))
        self.lewds.append('( ͡° ͜ʖ ͡°)')

    @commands.command()
    async def kyubey(self):
        """Madoka is best anime ever"""
        await self.bot.say('／人◕ ‿‿ ◕人＼')

    @commands.command()
    async def roll(self, dice: str):
        """Rolls a dice in NdN format."""
        try:
            rolls, limit = map(int, dice.split('d'))
        except Exception:
            await self.bot.say('Format has to be in NdN!')
            return

        result = ', '.join(str(random.randint(1, limit)) for _ in range(rolls))
        await self.bot.say(result)

    @commands.command()
    async def choose(self, *choices: str):
        """Chooses between multiple choices."""
        await self.bot.say(random.choice(choices))

    @commands.command()
    async def salt(self, percentage: str, tries: int):
        """ chance of an event happeneing """
        percentage = float(percentage.replace('%', '')) / 100 if '%' in percentage else float(percentage)
        res = round((1 - (1 - percentage) ** tries) * 100, 2)
        await self.bot.say('about {}% of dropping'.format(res))

    @commands.command()
    async def repeat(self, n: int, *message: str):
        """ repeat message n times, n <= 5 """
        if n > 5:
            await self.bot.say("Are you trying to break me?")
            return
        for _ in range(n):
            await self.bot.say(' '.join(message))

    @commands.command(pass_context=True)
    async def kanna(self, ctx):
        """
        Randomly display a kanna image to the channel
        :param ctx: Context
        :type ctx: ctx
        :return: nothing
        :rtype: None
        """
        fn = random.choice(self.kanna_files)
        await self.bot.send_file(ctx.message.channel, fn)

    @commands.command(pass_context=True)
    async def chensaw(self, ctx):
        """Display a chensaw gif"""
        await self.bot.send_file(ctx.message.channel, join('data', 'chensaw.gif'))

    @commands.command(pass_context=True)
    async def ayaya(self, ctx):
        """Ayaya!"""
        await self.bot.send_file(ctx.message.channel, join('data', 'ayaya.png'))

    @commands.command()
    async def lewd(self):
        """Display lewd reaction face"""
        await self.bot.say(random.choice(self.lewds))

    @commands.command()
    async def steamymeme(self):
        await self.bot.say(random.choice(['http://puu.sh/uvS7R/edce92064d.mp4', 'http://puu.sh/uvSOB/7e0ec82720.mp4']))
