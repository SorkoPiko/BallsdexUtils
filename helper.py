import imagehash, requests, cv2, numpy as np, json, typing
from PIL import Image
from io import BytesIO
from pymongo.collection import Collection
from pymongo.results import InsertOneResult, UpdateResult
from fractions import Fraction

DEFAULT_CONFIG = {
	'name': False,
	'reactions': True,
	}
BASE_POINTS = 1

class SetEncoder(json.JSONEncoder):
	def default(self, obj):
		if isinstance(obj, set):
			return {'__set__': list(obj)}
		return super().default(obj)

def set_decoder(dct):
	if "__set__" in dct:
		return set(dct["__set__"])
	return dct

def hashImageURL(url: str) -> imagehash.ImageHash:
	return imagehash.average_hash(urlToImage(url))

def urlToImage(url: str) -> Image.Image:
	return Image.open(BytesIO(requests.get(url).content))

def getAverageColour(image: Image.Image) -> int:
	npArray = np.average(np.average(cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR), axis=0), axis=0)
	return int(npArray[0]) << 16 | int(npArray[1]) << 8 | int(npArray[2])

def getNameDict(hashDB) -> dict[str, set[str]]:
	nameDict: dict[str, set[str]] = {}
	collection = find({}, hashDB)
	for document in collection:
		for name in document['names']:
			nameDict.update({name: document['_id']})
	return nameDict

def hamming_distance(x, y):
	binary_str1 = bin(int(x, 16))[2:].zfill(len(x) * 4)
	binary_str2 = bin(int(y, 16))[2:].zfill(len(y) * 4)

	# Calculate the Hamming distance
	hamming_distance = sum(bit1 != bit2 for bit1, bit2 in zip(binary_str1, binary_str2))

	return hamming_distance

def insertOne(insert: dict, collection: Collection) -> InsertOneResult:
	return collection.insert_one(json.loads(json.dumps(insert, cls=SetEncoder)))

def findOne(find: dict, collection: Collection) -> dict:
	return json.loads(json.dumps(collection.find_one(find)), object_hook=set_decoder)

def updateOne(find: dict, update: dict, collection: Collection, upsert: bool=False) -> UpdateResult:
	collection.update_one(find, json.loads(json.dumps(update, cls=SetEncoder)), upsert=upsert)

def updateNames(find: dict, update: dict, collection: Collection) -> UpdateResult:
	current = findOne(find, collection)
	current.update(update)
	updateOne(find, {'$set': json.loads(json.dumps(current, cls=SetEncoder))}, collection)

def find(query: dict, collection: Collection) -> list:
	result = collection.find(query)
	decoded_results = []
	for doc in result:
		decoded_data = json.loads(json.dumps(doc), object_hook=set_decoder)
		decoded_results.append(decoded_data)

	return decoded_results

def _configGet(configDB: Collection, id) -> dict:
	return findOne({'_id': id}, configDB)

def configCheck(configDB: Collection, guildID: int) -> dict:
	current = _configGet(configDB, guildID)
	if not current:
		_configCreate(configDB, guildID)
		current = _configGet(configDB, guildID)
	newConfig = DEFAULT_CONFIG.copy()
	newConfig.update(current)
	newConfig.pop('_id')
	updateOne({'_id': guildID}, {'$set': newConfig}, configDB)
	return _configGet(configDB, guildID)

def _configCreate(configDB: Collection, guildID: int, customConfig: dict=DEFAULT_CONFIG) -> int:
	customConfig['_id'] = guildID
	return insertOne(customConfig, configDB).inserted_id

def _configCheck(configDB: Collection, guildID: int) -> dict:
	return findOne({'_id': guildID}, configDB) is not None

def rarityCalc(rarity: float, shiny: bool=False):
	extra = 1
	if shiny:
		extra = 1/2048
	return round(BASE_POINTS / rarity / extra, 2)