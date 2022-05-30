# Release notes

<!-- do not remove -->

## 0.2.3

### New Features

- Improve performance by avoiding ORM loading of all data ([#53](https://github.com/somnathrakshit/geograpy3/issues/53))
  - **Is your feature request related to a problem? Please describe.**
Loading the LocationContext as objects in to main memory currently takes 4 seconds which is completly unnecessary for most usecases where only a few lookups are needed

**Describe the solution you'd like**
Allow for lazy loading via properties and lookup without using hashtables as the solution was a few weeks ago using SQLite access.



## 0.2.3

### New Features

- Improve performance by avoiding ORM loading of all data ([#53](https://github.com/somnathrakshit/geograpy3/issues/53))
  - **Is your feature request related to a problem? Please describe.**

Loading the LocationContext as objects in to main memory currently takes 4 seconds which is completly unnecessary for most usecases where only a few lookups are needed



**Describe the solution you'd like**

Allow for lazy loading via properties and lookup without using hashtables as the solution was a few weeks ago using SQLite access.



## 0.1.9

Fix version number


## 0.1.8

### New Features

- Add ISO country code ([#10](https://github.com/somnathrakshit/geograpy3/issues/10))
  - returned country information should include the two [letter ISO
    code](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2) of the
    country

- if country is given disambiguate country ([#7](https://github.com/somnathrakshit/geograpy3/issues/7))
  - see e.g. https://stackoverflow.com/questions/62152428/extracting-
    country-information-from-description-using-
    geograpy?noredirect=1#comment112899776_62152428    Zaragoza, Spain
    should e.g. only return the country Spain since it's in the
    context of Zaragoza

### Bugs Squashed

- [BUG]AttributeError: 'NoneType' object has no attribute 'name' on "Pristina, Kosovo" ([#9](https://github.com/somnathrakshit/geograpy3/issues/9))
  - **Describe the bug**  ```
    geograpy.get_geoPlace_context(text="Pristina, Kosovo")  ```  leads
    to python error.    **To Reproduce**  Steps to reproduce the
    behavior:  ```python  def testIssue(self):          '''
    test Issue          '''              locality="Pristina, Kosovo"
    gp=geograpy.get_geoPlace_context(text=locality)          if
    self.debug:              print("  %s" % gp.countries)
    print("  %s" % gp.regions)              print("  %s" % gp.cities)
    ```      File
    "/Users/wf/Documents/pyworkspace/geograpy3/geograpy/places.py",
    line 189, in set_cities      country_name = country.name
    AttributeError: 'NoneType' object has no attribute 'name'
    **Expected behavior**  Python should not choke on this although
    the political result may be disputed.

