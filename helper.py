import imagehash, requests, cv2, numpy as np
from PIL import Image
from io import BytesIO

def hashImageURL(url: str) -> imagehash.ImageHash:
	return imagehash.average_hash(urlToImage(url))

def urlToImage(url: str) -> Image.Image:
	return Image.open(BytesIO(requests.get(url).content))

def getAverageColour(image: Image.Image) -> int:
	npArray = np.average(np.average(cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR), axis=0), axis=0)
	return int(npArray[0]) << 16 | int(npArray[1]) << 8 | int(npArray[2])

def getNameDict(hashDB) -> dict[str, set[str]]:
	nameDict: dict[str, set[str]] = {}
	for document in hashDB.find({}):
		for name in document['names']:
			nameDict.update({name: document['_id']})
	return nameDict

def hamming_distance(x, y):
	return bin(x ^ y).count('1')