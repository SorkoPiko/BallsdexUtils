#import discord
from discord.ext import commands
from helper	import *
from main import BallsdexUtils

VERSION = "0.1.0"

class Admin(commands.Cog):
	def __init__(self, bot: BallsdexUtils):
		self.bot = bot
		self.bot.logger.info(f'Loaded Cog:{self.__cog_name__} v{VERSION}')

	@commands.command(name='reload', description='Reloads a cog.')
	@commands.is_owner()
	async def admin_reload(self, ctx: commands.Context, cog: str):
		try:
			self.bot.reload_extension(f'ext.{cog}')
		except commands.ExtensionNotLoaded:
			self.bot.load_extension(f'ext.{cog}')
		await ctx.send(f'Reloaded {cog}!')

async def setup(bot: BallsdexUtils):
	await bot.add_cog(Admin(bot))