import json
from urllib.request import urlopen
url = 'https://stac.dataspace.copernicus.eu/v1/collections/sentinel-2-l2a/items/S2B_MSIL2A_20241231T070219_N0511_R063_T40RBT_20241231T091815'
data = json.load(urlopen(url))
print(json.dumps({
  'id':data['id'],
  'bbox':data['bbox'],
  'properties':data['properties'],
  'B02_10m':data['assets']['B02_10m'],
  'B11_20m':data['assets']['B11_20m'],
}, indent=2))
