import discord, imagehash, json, requests, re, os
from discord.ext import commands
from PIL import Image
from io import BytesIO

intents = discord.Intents.all()

CAUGHT_PATTERN = r'<@!*\d+> You caught \*\*(.+)!\*\* \(`#(.+)`\)[\s\S]*'

activity = discord.Streaming(name="Ballsdex Answers", url="https://twitch.tv/SorkoPiko")
client = commands.Bot(command_prefix='?', intents=intents, activity=activity)

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
	return imagehash.average_hash(Image.open(BytesIO(requests.get(url).content)))

def identify(imageHash: imagehash.ImageHash):
	hashes = getHashes()
	if imageHash in hashes:
		return hashes[imageHash]['names']
	else:
		return None

@client.event
async def on_ready():
	await client.tree.sync()
	print('We\'re in')

@client.event
async def on_message(message: discord.Message):
	if message.author.id == 999736048596816014:
		if message.content == 'A wild countryball appeared!':
			imageHash = str(hashImageURL(message.attachments[0].url))

			hashes = getHashes()

			if imageHash in hashes and hashes[imageHash]['status'] == 'identified':
				await message.add_reaction('✅')
				await message.reply(f'Looks like {" or ".join([f"**{value}**" for value in hashes[imageHash]["names"]])}.')

			else:
				await message.add_reaction('🔄')
				# hashes[imageHash] = {'status': 'unidentified', 'message': message.id}
		else:
			caughtMatch = re.match(CAUGHT_PATTERN, message.content)
			print(message.content)
			print(message.flags)
			print(caughtMatch)
			if caughtMatch:
				print(caughtMatch.group(1))
				print('match!!')
				originalMessage = await message.channel.fetch_message(message.reference.message_id)
				imageHash = str(imagehash.average_hash(Image.open(BytesIO(requests.get(originalMessage.attachments[0].url).content))))
				hashes = getHashes()

				if imageHash in hashes:
					hashes[imageHash]['names'].add(caughtMatch.group(1))
					await message.add_reaction('✅')
				else:
					hashes[imageHash] = {'status': 'identified', 'names': {caughtMatch.group(1)}}
					await message.add_reaction('✅')
				
				saveHashes(hashes)

@client.tree.command()
async def add(interaction: discord.Interaction, image: discord.Attachment, names: str):
	if interaction.user.id == 609544328737456149:
		imageHash = str(hashImageURL(image.url))
		hashes = getHashes()
		if imageHash in hashes:
			hashes[imageHash]['names'].update(names.split(','))
		else:
			hashes[imageHash] = {'status': 'identified', 'names': set(names.split(','))}
		saveHashes(hashes)
		await interaction.response.send_message('Added!', ephemeral=True)

client.run(os.getenv('TOKEN'))