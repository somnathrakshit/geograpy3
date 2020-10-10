import geograpy
url='https://en.wikipedia.org/wiki/2012_Summer_Olympics_torch_relay'
places = geograpy.get_geoPlace_context(url = url)
print(places)
