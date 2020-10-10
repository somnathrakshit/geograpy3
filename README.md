# geograpy3
[![Join the chat at https://gitter.im/geograpy3/community](https://badges.gitter.im/geograpy3/community.svg)](https://gitter.im/geograpy3/community?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)
[![Documentation Status](https://readthedocs.org/projects/geograpy3/badge/?version=latest)](https://geograpy3.readthedocs.io/en/latest/?badge=latest)
[![pypi](https://img.shields.io/pypi/pyversions/geograpy3)](https://pypi.org/project/geograpy3/)
[![Github Actions Build](https://github.com/somnathrakshit/geograpy3/workflows/Build/badge.svg?branch=master)](https://github.com/somnathrakshit/geograpy3/actions?query=workflow%3ABuild+branch%3Amaster)
[![PyPI Status](https://img.shields.io/pypi/v/geograpy3.svg)](https://pypi.python.org/pypi/geograpy3/)
[![Downloads](https://pepy.tech/badge/geograpy3)](https://pepy.tech/project/geograpy3)
[![GitHub issues](https://img.shields.io/github/issues/somnathrakshit/geograpy3.svg)](https://github.com/somnathrakshit/geograpy3/issues)
[![GitHub closed issues](https://img.shields.io/github/issues-closed/somnathrakshit/geograpy3.svg)](https://github.com/somnathrakshit/geograpy3/issues/?q=is%3Aissue+is%3Aclosed)
[![License](https://img.shields.io/github/license/somnathrakshit/geograpy3.svg)](https://www.apache.org/licenses/LICENSE-2.0)


geograpy3 is a fork of [geograpy2](https://github.com/Corollarium/geograpy2), which is itself a fork of [geograpy](https://github.com/ushahidi/geograpy) and inherits
most of it, but solves several problems (such as support for utf8, places names
with multiple words, confusion over homonyms etc). Also, geograpy3 is compatible with Python 3, unlike geograpy2.

What it is
==========

geograpy extracts place names from a URL or text, and add context to those names -- for example distinguishing between a country, region or city.

## Examples/Tutorial
* [see Examples/Tutorial Wiki](http://wiki.bitplan.com/index.php/Geograpy#Examples)

## Install & Setup

Grab the package using `pip` (this will take a few minutes)
```bash
pip install geograpy3
```

geograpy3 uses [NLTK](http://www.nltk.org/) for entity recognition, so you'll also need
to download the models we're using. Fortunately there's a command that'll take
care of this for you.
```bash
geograpy-nltk
```

## Getting the source code
```bash
git clone https://github.com/somnathrakshit/geograpy3
cd geograpy3
scripts/install
```

## Basic Usage

Import the module, give some text or a URL, and presto.
```python
import geograpy
url = 'https://en.wikipedia.org/wiki/2012_Summer_Olympics_torch_relay'
places = geograpy.get_geoPlace_context(url=url)
```

Now you have access to information about all the places mentioned in the linked
article.

* `places.countries` _contains a list of country names_
* `places.regions` _contains a list of region names_
* `places.cities` _contains a list of city names_
* `places.other` _lists everything that wasn't clearly a country, region or city_

Note that the `other` list might be useful for shorter texts, to pull out
information like street names, points of interest, etc, but at the moment is
a bit messy when scanning longer texts that contain possessive forms of proper
nouns (like "Russian" instead of "Russia").

## But Wait, There's More

In addition to listing the names of discovered places, you'll also get some
information about the relationships between places.

* `places.country_regions` _regions broken down by country_
* `places.country_cities` _cities broken down by country_
* `places.address_strings` _city, region, country strings useful for geocoding_

## Last But Not Least

While a text might mention many places, it's probably focused on one or two, so
geograpy3 also breaks down countries, regions and cities by number of mentions.

* `places.country_mentions`
* `places.region_mentions`
* `places.city_mentions`

Each of these returns a list of tuples. The first item in the tuple is the place
name and the second item is the number of mentions. For example:

    [('Russian Federation', 14), (u'Ukraine', 11), (u'Lithuania', 1)]  

## If You're Really Serious

You can of course use each of Geograpy's modules on their own. For example:
```python
from geograpy import extraction

e = extraction.Extractor(url='https://en.wikipedia.org/wiki/2012_Summer_Olympics_torch_relay')
e.find_geoEntities()

# You can now access all of the places found by the Extractor
print(e.places)
```

Place context is handled in the `places` module. For example:

```python
from geograpy import places

pc = places.PlaceContext(['Cleveland', 'Ohio', 'United States'])

pc.set_countries()
print pc.countries #['United States']

pc.set_regions()
print(pc.regions #['Ohio'])

pc.set_cities()
print(pc.cities #['Cleveland'])

print(pc.address_strings #['Cleveland, Ohio, United States'])
```

And of course all of the other information shown above (`country_regions` etc)
is available after the corresponding `set_` method is called.

## Stackoverflow
* [Questions tagged with 'geograpy'](https://stackoverflow.com/questions/tagged/geograpy)

## Credits

geograpy3 uses the following excellent libraries:

* [NLTK](http://www.nltk.org/) for entity recognition
* [newspaper](https://github.com/codelucas/newspaper) for text extraction from HTML
* [jellyfish](https://github.com/sunlightlabs/jellyfish) for fuzzy text match
* [pylodstorage](https://pypi.org/project/pylodstorage/) for storage and retrieval of tabular data from SQL and SPARQL sources

geograpy3 uses the following data sources:
* [GeoLite2](http://dev.maxmind.com/geoip/geoip2/geolite2/) by MaxMind for city lookups
* [ISO3166ErrorDictionary](https://github.com/bodacea/countryname/blob/master/countryname/databases/ISO3166ErrorDictionary.csv) for common country mispellings _via [Sara-Jayne Terp](https://github.com/bodacea)_
* [pycountry](https://pypi.python.org/pypi/pycountry) for country/region lookups
* [Wikidata](https://www.wikidata.org) for country/region/city information with disambiguation details like population/gdpPerCapita

Hat tip to [Chris Albon](https://github.com/chrisalbon) for the name.
