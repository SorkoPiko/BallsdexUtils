import discord
from discord.ext import commands
from helper	import *
from main import BallsdexUtils
from discord import app_commands

VERSION = "0.1.0"

class Config(commands.GroupCog):
	def __init__(self, bot: BallsdexUtils):
		self.bot = bot
		self.bot.logger.info(f'Loaded Cog:{self.__cog_name__} v{VERSION}')

	@app_commands.command(name='name', description='Shows the balls\'s name.')
	@app_commands.describe(enabled='Whether to show the name or not.')
	async def config_name(self, interaction: discord.Interaction, enabled: bool):
		if enabled:
			updateOne({'_id': interaction.guild_id}, {'$set': {'name': True}}, self.bot.settingsDB)
			await interaction.response.send_message('Enabled showing the name.', ephemeral=True)
		else:
			updateOne({'_id': interaction.guild_id}, {'$set': {'name': False}}, self.bot.settingsDB)
			await interaction.response.send_message('Disabled showing the name.', ephemeral=True)

async def setup(bot: BallsdexUtils):
	await bot.add_cog(Config(bot))