import discord
from discord.ext import commands
from helper	import *
from main import BallsdexUtils
from discord import app_commands

VERSION = "0.3.0"

class Hash(commands.GroupCog):
	def __init__(self, bot: BallsdexUtils):
		self.bot = bot
		self.bot.logger.info(f'Loaded Cog:{self.__cog_name__} v{VERSION}')

	@app_commands.command(name='get', description='Get the hash of an image.')
	@app_commands.describe(image='The image to hash.')
	async def has_hget(self, interaction: discord.Interaction, image: discord.Attachment):
		if not image.content_type.startswith('image'):
			await interaction.response.send_message('Please attach an image to the command!', ephemeral=True)
			return
		imageHash = str(hashImageURL(image.url))
		embed = discord.Embed(title=f'{image.filename}', colour=discord.Colour(getAverageColour(urlToImage(image))))
		embed.set_image(url=image.url)
		embed.set_author(name=f'{interaction.user.display_name}', icon_url=interaction.user.display_avatar.url)
		embed.add_field(name='Image Hash', value=imageHash, inline=True)
		await interaction.response.send_message(embed=embed)

	@app_commands.command(name='compare', description='Compare two images\' hashes.')
	@app_commands.describe(image1='The first image to compare.', image2='The second image to compare.')
	async def hash_compare(self, interaction: discord.Interaction, image1: discord.Attachment, image2: discord.Attachment):
		if not image1.content_type.startswith('image') or not image2.content_type.startswith('image'):
			await interaction.response.send_message('Please attach images to the command!', ephemeral=True)
			return
		imageHash = str(hashImageURL(image1.url))
		image2Hash = str(hashImageURL(image2.url))
		embed = discord.Embed(title=f'{image1.filename}', colour=discord.Colour(getAverageColour(urlToImage(image1))))
		embed.set_image(url=image2.url)
		embed.set_thumbnail(url=image1.url)
		embed.set_author(name=f'{interaction.user.display_name}', icon_url=interaction.user.display_avatar.url)
		embed.add_field(name='Image 1 Hash', value=imageHash, inline=True)
		embed.add_field(name='Image 2 Hash', value=image2Hash, inline=True)
		embed.add_field(name='Hamming Distance', value=hamming_distance(imageHash, image2Hash), inline=True)
	
async def setup(bot: BallsdexUtils):
	await bot.add_cog(Hash(bot))