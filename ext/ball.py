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

	@app_commands.command(name='info', description='Get info on a ball.')
	@app_commands.describe(ball='The ball to get info on.')
	async def ball_info(self, interaction: discord.Interaction, ball: str):
		nameDict = getNameDict(self.bot.hashDB)
		if ball not in nameDict:
			await interaction.response.send_message('Either that ball doesn\'t exist or I don\'t know it!\nIf it does exist, it\'ll be added as soon as someone catches it.', ephemeral=True)
		embed = discord.Embed(title=f'{ball}', colour=discord.Colour.random())
		embed.set_author(name=f'{interaction.user.display_name}', icon_url=interaction.user.display_avatar.url)
		embed.add_field(name='Image Hash', value=nameDict[ball], inline=True)
		embed.add_field(name='Names', value=', '.join(findOne({'_id': nameDict[ball]}, self.bot.hashDB)['names']), inline=True)
		await interaction.response.send_message(embed=embed)

	@ball_info.autocomplete('ball')
	async def info_autocomplete(self, interaction: discord.Interaction, current: str) -> typing.List[discord.app_commands.Choice[str]]:
		nameDict = getNameDict(self.bot.hashDB)
		print(nameDict)
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
		embed.set_author(name=f'{interaction.user.display_name}', icon_url=interaction.user.display_avatar.url)
		embed.add_field(name='Image Hash', value=imageHash, inline=True)
		embed.add_field(name='Names', value=', '.join(result['names']), inline=True)
		await interaction.response.send_message(embed=embed)

async def setup(bot: BallsdexUtils):
	await bot.add_cog(Ball(bot))