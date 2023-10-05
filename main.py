import discord, imagehash, requests, re, os, typing, cv2
from discord.ext import commands
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv
import numpy as np
from pymongo import MongoClient

load_dotenv()
# Setup MongoDB connection
client = MongoClient(os.getenv('MONGO_URI'))
db = client['main']
hashDB = db['hashes']
intents = discord.Intents.all()

CAUGHT_PATTERN = r'<@!*\d+> You caught \*\*(.+)!\*\* \(`#(.+)`\)[\s\S]*'

activity = discord.Streaming(name="Ballsdex Answers", url="https://twitch.tv/SorkoPiko")
bot = commands.Bot(command_prefix='bs!', intents=intents, activity=activity)

def hashImageURL(url: str) -> imagehash.ImageHash:
	return imagehash.average_hash(urlToImage(url))

def urlToImage(url: str) -> Image.Image:
	return Image.open(BytesIO(requests.get(url).content))

def getAverageColour(image: Image.Image) -> int:
	npArray = np.average(np.average(cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR), axis=0), axis=0)
	return int(npArray[0]) << 16 | int(npArray[1]) << 8 | int(npArray[2])

def getNameDict():
	nameDict: dict[str, set[str]] = {}
	for document in hashDB.find({}):
		for name in document['names']:
			nameDict.update({name: document['_id']})
	return nameDict

def hamming_distance(x, y):
  return bin(x ^ y).count('1')

@bot.event
async def on_ready():
	await bot.tree.sync()
	print('We\'re in')

@bot.listen('on_message')
async def ballsdexCheck(message: discord.Message):
	if message.author.id == 999736048596816014 and message.content == 'A wild countryball appeared!':
		imageHash = str(hashImageURL(message.attachments[0].url))
		dbEntry = hashDB.find_one({'_id': imageHash})

		if dbEntry:
			await message.add_reaction('✅')
			await message.reply(f'Looks like {" or ".join([f"**{value}**" for value in dbEntry["names"]])}.')

		else:
			await message.add_reaction('🔄')

@bot.listen('on_raw_message_edit')
async def ballsdexAdd(messageEvent: discord.RawMessageUpdateEvent):
	if messageEvent.data['author']['id'] == "999736048596816014":
		caughtMatch = re.match(CAUGHT_PATTERN, messageEvent.data['content'])
		if caughtMatch:
			print(f'Caught {caughtMatch.group(1)} ({messageEvent.message_id})')
			channel = await bot.fetch_channel(messageEvent.channel_id)
			message = await channel.fetch_message(messageEvent.message_id)
			originalMessage = await channel.fetch_message(messageEvent.data['message_reference']['message_id'])
			imageHash = str(imagehash.average_hash(Image.open(BytesIO(requests.get(originalMessage.attachments[0].url).content))))

			dbEntry = hashDB.find_one({'_id': imageHash})

			if dbEntry:
				hashDB.update_one({'_id': imageHash}, {'$addToSet': {'names': caughtMatch.group(1)}})
				await message.add_reaction('✅')
			else:
				hashDB.insert_one({'_id': imageHash, 'names': {caughtMatch.group(1)}})
				await message.add_reaction('✅')

@bot.tree.command(name='info')
async def info(interaction: discord.Interaction, ball: str):
	nameDict = getNameDict()
	if ball not in nameDict:
		await interaction.response.send_message('Either that ball doesn\'t exist or I don\'t know it!\nIf it does exist, it\'ll be added as soon as someone catches it.', ephemeral=True)
	embed = discord.Embed(title=f'{ball}', colour=discord.Colour.random())
	embed.set_author(name=f'{interaction.user.display_name}', icon_url=interaction.user.display_avatar.url)
	embed.add_field(name='Image Hash', value=nameDict[ball], inline=True)
	embed.add_field(name='Names', value=', '.join(hashDB.find_one({'_id': nameDict[ball]})['names']), inline=True)
	await interaction.response.send_message(embed=embed)

@info.autocomplete('ball')
async def info_autocomplete(interaction: discord.Interaction, current: str) -> typing.List[discord.app_commands.Choice[str]]:
	nameDict = getNameDict()

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

@bot.tree.command(name='identify')
@discord.app_commands.describe(ball='The ball to identify.')
async def identify(interaction: discord.Interaction, ball: discord.Attachment):
	if not ball.content_type.startswith('image'):
		await interaction.response.send_message('Please attach an image to the command!', ephemeral=True)
		return
	imageHash = str(hashImageURL(ball.url))

	result = hashDB.find_one({'_id': imageHash})

	if not result:
		await interaction.response.send_message('Either that ball doesn\'t exist or I don\'t know it!\nIf it does exist, it\'ll be added as soon as someone catches it.', ephemeral=True)
		return
	embed = discord.Embed(title=f'{ball.filename}', colour=discord.Colour(getAverageColour(urlToImage(ball))))
	embed.set_image(url=ball.url)
	embed.set_author(name=f'{interaction.user.display_name}', icon_url=interaction.user.display_avatar.url)
	embed.add_field(name='Image Hash', value=imageHash, inline=True)
	embed.add_field(name='Names', value=', '.join(result['names']), inline=True)
	await interaction.response.send_message(embed=embed)

@bot.tree.command(name='hash')
@discord.app_commands.describe(image='The image to hash.')
async def hash(interaction: discord.Interaction, image: discord.Attachment):
	if not image.content_type.startswith('image'):
		await interaction.response.send_message('Please attach an image to the command!', ephemeral=True)
		return
	imageHash = str(hashImageURL(image.url))
	embed = discord.Embed(title=f'{image.filename}', colour=discord.Colour(getAverageColour(urlToImage(image))))
	embed.set_image(url=image.url)
	embed.set_author(name=f'{interaction.user.display_name}', icon_url=interaction.user.display_avatar.url)
	embed.add_field(name='Image Hash', value=imageHash, inline=True)
	await interaction.response.send_message(embed=embed)

@bot.tree.command(name='hammingDistance')
@discord.app_commands.describe(image1='The first image to compare.', image2='The second image to compare.')
async def hammingDistance(interaction: discord.Interaction, image: discord.Attachment, image2: discord.Attachment):
	if not image.content_type.startswith('image') or not image2.content_type.startswith('image'):
		await interaction.response.send_message('Please attach images to the command!', ephemeral=True)
		return
	imageHash = str(hashImageURL(image.url))
	image2Hash = str(hashImageURL(image2.url))
	embed = discord.Embed(title=f'{image.filename}', colour=discord.Colour(getAverageColour(urlToImage(image))))
	embed.set_image(url=image2.url)
	embed.set_thumbnail(url=image.url)
	embed.set_author(name=f'{interaction.user.display_name}', icon_url=interaction.user.display_avatar.url)
	embed.add_field(name='Image 1 Hash', value=imageHash, inline=True)
	embed.add_field(name='Image 2 Hash', value=image2Hash, inline=True)
	embed.add_field(name='Hamming Distance', value=hamming_distance(imageHash, image2Hash), inline=True)

bot.run(os.getenv('TOKEN'))