import discord, re
from discord.ext import commands
from helper	import *
from main import BallsdexUtils

VERSION = "1.1.0"

class Listeners(commands.Cog):
	def __init__(self, bot: BallsdexUtils):
		self.bot = bot
		self.bot.logger.info(f'Loaded Cog:{self.__cog_name__} v{VERSION}')
		
	@commands.Cog.listener('on_message')
	async def ballsdexCheck(self, message: discord.Message):
		if message.author.id == self.bot.BALLSDEX_ID and message.content == 'A wild countryball appeared!':
			imageHash = str(hashImageURL(message.attachments[0].url))
			dbEntry = self.bot.hashDB.find_one({'_id': imageHash})

			if dbEntry:
				await message.add_reaction('✅')
				await message.reply(f'Looks like {" or ".join([f"**{value}**" for value in dbEntry["names"]])}.')

			else:
				await message.add_reaction('🔄')

	@commands.Cog.listen('on_raw_message_edit')
	async def ballsdexAdd(self, messageEvent: discord.RawMessageUpdateEvent):
		if int(messageEvent.data['author']['id']) == self.bot.BALLSDEX_ID:
			caughtMatch = re.match(self.bot.CAUGHT_PATTERN, messageEvent.data['content'])
			if caughtMatch:
				print(f'Caught {caughtMatch.group(1)} ({messageEvent.message_id})')
				channel = await self.bot.fetch_channel(messageEvent.channel_id)
				message = await channel.fetch_message(messageEvent.message_id)
				originalMessage = await channel.fetch_message(messageEvent.data['message_reference']['message_id'])
				imageHash = str(imagehash.average_hash(Image.open(BytesIO(requests.get(originalMessage.attachments[0].url).content))))

				dbEntry = self.bot.hashDB.find_one({'_id': imageHash})

				if dbEntry:
					self.bot.hashDB.update_one({'_id': imageHash}, {'$addToSet': {'names': caughtMatch.group(1)}})
					await message.add_reaction('✅')
				else:
					self.bot.hashDB.insert_one({'_id': imageHash, 'names': {caughtMatch.group(1)}})
					await message.add_reaction('✅')