import geograpy
url='https://www.bbc.com/news/uk-13426353'
places = geograpy.get_geoPlace_context(url = url)
print(places)
