from setuptools import setup
import pathlib
import pkg_resources
import os 
from collections import OrderedDict
import configparser

config = configparser.ConfigParser()
config.read('settings.ini')

with pathlib.Path(os.path.join(os.path.dirname(__file__), 'requirements.txt')).open() as requirements_txt:
    install_requires = [
        str(requirement)
        for requirement
        in pkg_resources.parse_requirements(requirements_txt)
    ]
        
try:
    long_description = ""
    with open('README.md', encoding='utf-8') as f:
        long_description = f.read()

except:
    print('Curr dir:', os.getcwd())
    long_description = open('../../README.md').read()

setup(name='geograpy3',
      version=config["DEFAULT"]["version"],
      description='Extract countries, regions and cities from a URL or text',
      long_description=long_description,
      long_description_content_type='text/markdown',
      url='https://github.com/somnathrakshit/geograpy3',
      download_url='https://github.com/somnathrakshit/geograpy3',
      author='Somnath Rakshit',
      author_email='somnath52@gmail.com',
      license='Apache',
      project_urls=OrderedDict(
        (
            ("Documentation", "https://geograpy3.readthedocs.io"),
            ("Code", "https://github.com/somnathrakshit/geograpy3"),
            ("Issue tracker", "https://github.com/somnathrakshit/geograpy3/issues"),
        )
      ),
      classifiers=[
            'Programming Language :: Python',
            'Programming Language :: Python :: 3.7',
            'Programming Language :: Python :: 3.8',
            'Programming Language :: Python :: 3.9',
            'Programming Language :: Python :: 3.10',
            'Programming Language :: Python :: 3.11'
      ],
      packages=['geograpy'],
      install_requires=install_requires,
      package_data={
          'geograpy': ['data/*.csv'],
      },
      zip_safe=False)
