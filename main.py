import discord, os, logging, logging.handlers
from discord.ext import commands
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv
import numpy as np
from pymongo import MongoClient

EXTENSIONS = [
	'ext.hash',
	'ext.ball',
	'ext.listeners',
	'ext.config',
	'ext.admin',
	'jishaku'
]

class BallsdexUtils(commands.AutoShardedBot):
	def __init__(self):
		self.client = MongoClient(os.getenv('MONGO_URI'))
		self.mainDB = self.client['main']
		self.lbDB = self.mainDB['leaderboard']
		self.hashDB = self.mainDB['hashes']
		self.raritiesDB = self.mainDB['rarity']
		self.configDB = self.mainDB['config']
		self.CAUGHT_PATTERN = r'<@!*(\d+)> You caught \*\*(.+)!\*\* \(`#(.+)`\)[\s\S]*'
		self.BALLSDEX_ID = 999736048596816014
		intents=discord.Intents.default()
		intents.message_content = True
		# handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
		logger = logging.getLogger('discord')
		logger.setLevel(logging.DEBUG)
		logging.getLogger('discord.http').setLevel(logging.INFO)
		logging.getLogger('discord.gateway').setLevel(logging.INFO)
		if not os.path.exists('./logs'):
			os.mkdir('logs')
		handler = logging.handlers.RotatingFileHandler(
			filename='logs/discord.log',
			encoding='utf-8',
			maxBytes=32 * 1024 * 1024,  # 32 MiB
			backupCount=5,  # Rotate through 5 files
		)
		dt_fmt = '%Y-%m-%d %H:%M:%S'
		formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', dt_fmt, style='{')
		handler.setFormatter(formatter)
		logger.addHandler(handler)
		activity = discord.Streaming(name="Ballsdex Answers", url="https://twitch.tv/SorkoPiko")
		super().__init__(command_prefix='bs!', intents=intents, help_command=None, activity=activity)

		self.logger = logger
	
	async def on_ready(self):
		for extension in EXTENSIONS:
			await self.load_extension(extension)
		self.logger.info(f"Logged in as {self.user}")
		print(f"Logged in as {self.user}")

if __name__ == '__main__':
	os.chdir(os.path.dirname(os.path.abspath(__file__)))
	load_dotenv()
	bot = BallsdexUtils()
	bot.run(os.getenv('TOKEN'))