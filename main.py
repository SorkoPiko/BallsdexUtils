import discord, imagehash, json, requests, re, os
from discord.ext import commands
from PIL import Image
from io import BytesIO

intents = discord.Intents.default()
intents.message_content = True

CAUGHT_PATTERN = r'<@!*\d+> You caught \*\*(.+)!\*\* \(`#(.+)`\)[\s\S]*'

client = commands.Bot(command_prefix='bs!', intents=intents)

@client.event
async def on_ready():
	await client.tree.sync()
	print('We\'re in')

@client.event
async def on_message(message: discord.Message):
	if message.author.id == 999736048596816014:
		if message.content == 'A wild countryball appeared!':
			imageHash = imagehash.average_hash(Image.open(BytesIO(requests.get(message.attachments[0].url).content)))

			with open('db.json', 'r') as f:
				hashes: dict[imagehash.ImageHash, dict[str, set]] = json.loads(f.read())

			if imageHash in hashes and hashes[imageHash]['status'] == 'identified':
				await message.add_reaction('✅')
				await message.reply(f'Looks like {" or ".join([f"**{value}**" for value in hashes[imageHash]["names"]])}.')

			else:
				await message.add_reaction('🔄')
				# hashes[imageHash] = {'status': 'unidentified', 'message': message.id}
		else:
			caughtMatch = re.match(CAUGHT_PATTERN, message.content)
			if caughtMatch:
				with open('db.json', 'r') as f:
					hashes: dict[imagehash.ImageHash, dict] = json.loads(f.read())

				originalMessage = await message.channel.fetch_message(message.reference.message_id)
				imageHash = imagehash.average_hash(Image.open(BytesIO(requests.get(originalMessage.attachments[0].url).content)))
				if imageHash in hashes:
					hashes[imageHash]['names'].append(caughtMatch.group(1))
				hashes[imageHash] = {'status': 'identified'}

client.run(os.getenv('TOKEN'))