import discord, imagehash, json, requests, re, os
from discord.ext import commands
from PIL import Image
from io import BytesIO

intents = discord.Intents.default()
intents.message_content = True

CAUGHT_PATTERN = r'<@!*\d+> You caught \*\*(.+)!\*\* \(`#(.+)`\)[\s\S]*'

activity = discord.Streaming(name="Ballsdex Answers", url="https://twitch.tv/SorkoPiko")
client = commands.Bot(command_prefix='bs!', intents=intents, activity=activity)

class SetEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return super().default(obj)

class SetDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        super().__init__(object_hook=self.set_hook, *args, **kwargs)
        
    def set_hook(self, dct):
        if "__set__" in dct:
            return set(dct["__set__"])
        return dct

def getHashes() -> dict[imagehash.ImageHash, dict['names': set[str]]]:
	with open('db.json', 'r') as f:
		return json.loads(f.read(), cls=SetDecoder)

def saveHashes(hashes: dict[imagehash.ImageHash, dict]) -> None:
	with open('db.json', 'w') as f:
		f.write(json.dumps(hashes, cls=SetEncoder))

def hashImageURL(url: str) -> imagehash.ImageHash:
	return imagehash.average_hash(Image.open(BytesIO(requests.get(url).content)))

def identify(imageHash: imagehash.ImageHash):
	hashes = getHashes()
	if imageHash in hashes:
		return hashes[imageHash]['names']
	else:
		return None

@client.command(name='add', alias=['a'])
@commands.is_owner()
async def add(url, *names):
	imageHash = hashImageURL(url)
	hashes = getHashes()
	if imageHash in hashes:
		hashes[imageHash]['names'].update(names)
	hashes[imageHash] = {'status': 'identified', 'names': names}
	saveHashes(hashes)

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
			if caughtMatch:
				hashes = getHashes()
				originalMessage = await message.channel.fetch_message(message.reference.message_id)
				imageHash = str(imagehash.average_hash(Image.open(BytesIO(requests.get(originalMessage.attachments[0].url).content))))

				if imageHash in hashes:
					if caughtMatch.group(1) not in hashes[imageHash]['names']:
						hashes[imageHash]['names'].append(caughtMatch.group(1))
						await message.add_reaction('✅')
				else:
					hashes[imageHash] = {'status': 'identified', 'names': {caughtMatch.group(1)}}
					await message.add_reaction('✅')
				
				saveHashes(hashes)

client.run(os.getenv('TOKEN'))