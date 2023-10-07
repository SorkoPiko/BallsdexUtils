import discord, typing
from discord.ext import commands
from helper	import *
from main import BallsdexUtils
from discord import app_commands

VERSION = "0.5.0"

class Ball(commands.GroupCog):
	def __init__(self, bot: BallsdexUtils):
		self.bot = bot
		self.bot.logger.info(f'Loaded Cog:{self.__cog_name__} v{VERSION}')

	async def info_autocomplete(self, interaction: discord.Interaction, current: str) -> typing.List[discord.app_commands.Choice[str]]:
		nameDict = getNameDict(self.bot.hashDB)
		if not current:
			return [
				discord.app_commands.Choice(name=ball, value=ball)
				for ball in nameDict.keys()
			][:25]
		return [
			discord.app_commands.Choice(name=ball, value=ball)
			for ball in nameDict.keys()
			if ball.lower().startswith(current.lower())
		][:25]

	@app_commands.command(name='info', description='Get info on a ball.')
	@app_commands.describe(ball='The ball to get info on.')
	@app_commands.autocomplete(ball=info_autocomplete)
	async def ball_info(self, interaction: discord.Interaction, ball: str):
		nameDict = getNameDict(self.bot.hashDB)
		if ball not in nameDict:
			await interaction.response.send_message('Either that ball doesn\'t exist or I don\'t know it!\nIf it does exist, it\'ll be added as soon as someone catches it.', ephemeral=True)
		embed = discord.Embed(title=f'{ball}', colour=discord.Colour.random())
		embed.add_field(name='Image Hash', value=nameDict[ball], inline=True)
		embed.add_field(name='Names', value=', '.join(findOne({'_id': nameDict[ball]}, self.bot.hashDB)['names']), inline=True)
		await interaction.response.send_message(embed=embed)

	@app_commands.command(name='identify', description='Identify a ball.')
	@app_commands.describe(ball='The ball to identify.')
	async def ball_identify(self, interaction: discord.Interaction, ball: discord.Attachment):
		if not ball.content_type.startswith('image'):
			await interaction.response.send_message('Please attach an image to the command!', ephemeral=True)
			return
		imageHash = str(hashImageURL(ball.url))

		result = findOne({'_id': imageHash}, self.bot.hashDB)

		if not result:
			await interaction.response.send_message('Either that ball doesn\'t exist or I don\'t know it!\nIf it does exist, it\'ll be added as soon as someone catches it.', ephemeral=True)
			return
		embed = discord.Embed(title=f'{ball.filename}', colour=discord.Colour(getAverageColour(urlToImage(ball))))
		embed.set_image(url=ball.url)
		embed.add_field(name='Image Hash', value=imageHash, inline=True)
		embed.add_field(name='Names', value=', '.join(result['names']), inline=True)
		await interaction.response.send_message(embed=embed)

	@app_commands.command(name='compare', description='Compare two balls\' hashes.')
	@app_commands.describe(ball1='The first ball to compare.', ball2='The second ball to compare.')
	@app_commands.autocomplete(ball1=info_autocomplete, ball2=info_autocomplete)
	async def ball_compare(self, interaction: discord.Interaction, ball1: str, ball2: str):
		nameDict = getNameDict(self.bot.hashDB)
		if ball1 not in nameDict or ball2 not in nameDict:
			await interaction.response.send_message('Either that ball doesn\'t exist or I don\'t know it!\nIf it does exist, it\'ll be added as soon as someone catches it.', ephemeral=True)
			return
		ball1Hash = nameDict[ball1]
		ball2Hash = nameDict[ball2]
		embed = discord.Embed(title=f'Hash Compare', colour=discord.Colour.random())
		embed.add_field(name=f'{ball1} Hash', value=ball1Hash, inline=True)
		embed.add_field(name=f'{ball2} Hash', value=ball2Hash, inline=True)
		embed.add_field(name='Hamming Distance', value=hamming_distance(ball1Hash, ball2Hash), inline=True)
		await interaction.response.send_message(embed=embed)

async def setup(bot: BallsdexUtils):
	await bot.add_cog(Ball(bot))