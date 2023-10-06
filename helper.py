import imagehash, requests, cv2, numpy as np, json
from PIL import Image
from io import BytesIO
from pymongo.collection import Collection

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

def insertOne(insert: dict, collection: Collection):
	return collection.insert_one(json.loads(json.dumps(insert, cls=SetEncoder)))

def findOne(find: dict, collection: Collection):
	return json.loads(json.dumps(collection.find_one(find)), object_hook=set_decoder)

def updateOne(find: dict, update: dict, collection: Collection):
	collection.update_one(find, json.loads(json.dumps(update, cls=SetEncoder)))

def find(query: dict, collection: Collection):
	result = collection.find(query)
	decoded_results = []
	for doc in result:
		decoded_data = json.loads(json.dumps(doc), object_hook=set_decoder)
		decoded_results.append(decoded_data)

	return decoded_results