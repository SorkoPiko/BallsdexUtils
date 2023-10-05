import discord, imagehash, json, requests, re, os, typing, cv2, logging
from discord.ext import commands
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv
import numpy as np

load_dotenv()

intents = discord.Intents.all()

CAUGHT_PATTERN = r'<@!*\d+> You caught \*\*(.+)!\*\* \(`#(.+)`\)[\s\S]*'

activity = discord.Streaming(name="Ballsdex Answers", url="https://twitch.tv/SorkoPiko")
client = commands.Bot(command_prefix='bs!', intents=intents, activity=activity)

class CustomJSONEncoder(json.JSONEncoder):
	def default(self, obj):
		if isinstance(obj, set):
			return {'__set__': list(obj)}
		return super().default(obj)

# Custom JSON decoder with support for sets
def custom_decoder(dct):
	if '__set__' in dct:
		return set(dct['__set__'])
	return dct

def getHashes() -> dict[imagehash.ImageHash, dict]:
	with open('db.json', 'r') as f:
		return json.loads(f.read(), object_hook=custom_decoder)

def saveHashes(hashes: dict[imagehash.ImageHash, dict]) -> None:
	with open('db.json', 'w') as f:
		f.write(json.dumps(hashes, cls=CustomJSONEncoder))

def hashImageURL(url: str) -> imagehash.ImageHash:
	return imagehash.average_hash(urlToImage(url))

def urlToImage(url: str) -> Image.Image:
	return Image.open(BytesIO(requests.get(url).content))

def getAverageColour(image: Image.Image) -> int:
	npArray = np.average(np.average(cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR), axis=0), axis=0)
	return int(npArray[0]) << 16 | int(npArray[1]) << 8 | int(npArray[2])

def getNameDict():
	nameDict = {}
	for hash, info in getHashes().items():
		for name in info['names']:
			nameDict.update({name: hash})
	return nameDict

@client.event
async def on_ready():
	await client.tree.sync()
	print('We\'re in')

@client.listen('on_message')
async def ballsdexCheck(message: discord.Message):
	if message.author.id == 999736048596816014 and message.content == 'A wild countryball appeared!':
		imageHash = str(hashImageURL(message.attachments[0].url))

		hashes = getHashes()

		if imageHash in hashes and hashes[imageHash]['status'] == 'identified':
			await message.add_reaction('✅')
			await message.reply(f'Looks like {" or ".join([f"**{value}**" for value in hashes[imageHash]["names"]])}.')

		else:
			await message.add_reaction('🔄')
			# hashes[imageHash] = {'status': 'unidentified', 'message': message.id}

@client.listen('on_raw_message_edit')
async def ballsdexAdd(message: discord.RawMessageUpdateEvent):
	if message.data['author']['id'] == 999736048596816014:
		if not message.cached_message:
			cached: discord.Message = await client.fetch_channel(message.channel_id).fetch_message(message.message_id)
		else: cached = message.cached_message
		caughtMatch = re.match(CAUGHT_PATTERN, cached.content)
		if caughtMatch:
			print(f'Caught {caughtMatch.group(1)} ({cached.id})')
			originalMessage = await cached.channel.fetch_message(cached.reference.message_id)
			imageHash = str(imagehash.average_hash(Image.open(BytesIO(requests.get(originalMessage.attachments[0].url).content))))
			hashes = getHashes()

			if imageHash in hashes:
				hashes[imageHash]['names'].add(caughtMatch.group(1))
				await cached.add_reaction('✅')
			else:
				hashes[imageHash] = {'status': 'identified', 'names': {caughtMatch.group(1)}}
				await cached.add_reaction('✅')
		
			saveHashes(hashes)

@client.command(name='add')
@commands.is_owner()
async def add(ctx: commands.Context, *names: str):
	names = ' '.join(names)
	if not ctx.message.attachments[0]:
		await ctx.send('Please attach an image to the command!', ephemeral=True)
		return
	imageHash = str(hashImageURL(ctx.message.attachments[0].url))
	hashes = getHashes()
	if imageHash in hashes:
		hashes[imageHash]['names'].update(names.split(','))
	else:
		hashes[imageHash] = {'status': 'identified', 'names': set(names.split(','))}
	saveHashes(hashes)
	await ctx.send(f'Added {names} to {imageHash}!', ephemeral=True)

@client.tree.command(name='info')
async def info(interaction: discord.Interaction, ball: str):
	nameDict = getNameDict()
	embed = discord.Embed(title=f'{ball}', colour=discord.Colour.random())
	embed.set_author(name=f'{interaction.user.display_name}', icon_url=interaction.user.display_avatar.url)
	embed.add_field(name='Image Hash', value=nameDict[ball], inline=True)
	embed.add_field(name='Names', value=', '.join(getHashes()[nameDict[ball]]['names']), inline=True)
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

@client.tree.command(name='identify')
async def identify(interaction: discord.Interaction, ball: discord.Attachment):
	if not ball.content_type.startswith('image'):
		await interaction.response.send_message('Please attach an image to the command!', ephemeral=True)
		return
	imageHash = str(hashImageURL(ball.url))
	hashes = getHashes()
	if imageHash not in hashes:
		await interaction.response.send_message('Either that ball doesn\'t exist or I don\'t know it!\nIf it does exist, it\'ll be added as soon as someone catches it.', ephemeral=True)
		return
	embed = discord.Embed(title=f'{ball.filename}', colour=discord.Colour(getAverageColour(urlToImage(ball))))
	embed.set_image(url=ball.url)
	embed.set_author(name=f'{interaction.user.display_name}', icon_url=interaction.user.display_avatar.url)
	embed.add_field(name='Image Hash', value=imageHash, inline=True)
	embed.add_field(name='Names', value=', '.join(hashes[imageHash]['names']), inline=True)
	await interaction.response.send_message(embed=embed)

@client.tree.command(name='hash')
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

client.run(os.getenv('TOKEN'))