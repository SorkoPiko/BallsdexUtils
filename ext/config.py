import discord
from discord.ext import commands
from helper	import *
from main import BallsdexUtils
from discord import app_commands

VERSION = "0.1.0"
CONFIG_NAMES = {
	'name': 'Names',
	'reactions': 'Reactions',
}
BOOL_NAMES = {
	True: 'Enabled',
	False: 'Disabled',
}

@app_commands.default_permissions(manage_guild=True)
class Config(commands.GroupCog):
	def __init__(self, bot: BallsdexUtils):
		self.bot = bot
		self.bot.logger.info(f'Loaded Cog:{self.__cog_name__} v{VERSION}')

	@app_commands.command(name='view', description='View the config.')
	async def config_view(self, interaction: discord.Interaction):
		config = configCheck(self.bot.configDB, interaction.guild_id)
		config.pop('_id')
		embed = discord.Embed(title='Config', colour=discord.Colour.green())
		embed.description = '\n'.join([f'**{CONFIG_NAMES[key]}:** {BOOL_NAMES[value]}' for key, value in config.items()])
		await interaction.response.send_message(embed=embed, ephemeral=True)

	@app_commands.command(name='name', description='Shows the balls\'s name.')
	@app_commands.describe(enabled='Whether to show the name or not.')
	async def config_name(self, interaction: discord.Interaction, enabled: bool):
		configCheck(self.bot.configDB, interaction.guild_id)
		if enabled:
			updateOne({'_id': interaction.guild_id}, {'$set': {'name': True}}, self.bot.configDB)
			await interaction.response.send_message('Enabled showing the name.', ephemeral=True)
		else:
			updateOne({'_id': interaction.guild_id}, {'$set': {'name': False}}, self.bot.configDB)
			await interaction.response.send_message('Disabled showing the name.', ephemeral=True)

async def setup(bot: BallsdexUtils):
	await bot.add_cog(Config(bot))