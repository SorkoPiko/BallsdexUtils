import discord, imagehash, json, requests, re, os
from discord.ext import commands
from PIL import Image
from io import BytesIO

intents = discord.Intents.default()
intents.message_content = True

CAUGHT_PATTERN = r'<@!*\d+> You caught \*\*(.+)!\*\* \(`#(.+)`\)[\s\S]*'

activity = discord.Streaming(name="Ballsdex Answers", url="https://twitch.tv/SorkoPiko")
client = commands.Bot(command_prefix='bs!', intents=intents)

def getHashes() -> dict[imagehash.ImageHash, dict['names': set[str]]]:
	with open('db.json', 'r') as f:
		return json.loads(f.read())

def saveHashes(hashes: dict[imagehash.ImageHash, dict]) -> None:
	with open('db.json', 'w') as f:
		f.write(json.dumps(hashes))

@client.event
async def on_ready():
	await client.tree.sync()
	print('We\'re in')

@client.event
async def on_message(message: discord.Message):
	if message.author.id == 999736048596816014:
		if message.content == 'A wild countryball appeared!':
			imageHash = imagehash.average_hash(Image.open(BytesIO(requests.get(message.attachments[0].url).content)))

			hashes = getHashes()

			if imageHash in hashes and hashes[imageHash]['status'] == 'identified':
				await message.add_reaction('✅')
				await message.reply(f'Looks like {" or ".join([f"**{value}**" for value in hashes[imageHash]["names"]])}.')

			else:
				await message.add_reaction('🔄')
				# hashes[imageHash] = {'status': 'unidentified', 'message': message.id}
		else:
			caughtMatch = re.match(CAUGHT_PATTERN, message.content)
			if caughtMatch:
				hashes = getHashes()
				originalMessage = await message.channel.fetch_message(message.reference.message_id)
				imageHash = imagehash.average_hash(Image.open(BytesIO(requests.get(originalMessage.attachments[0].url).content)))

				if imageHash in hashes:
					hashes[imageHash]['names'].add(caughtMatch.group(1))
				else:
					hashes[imageHash] = {'status': 'identified', 'names': {caughtMatch.group(1)}}

client.run(os.getenv('TOKEN'))