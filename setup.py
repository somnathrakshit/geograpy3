from setuptools import setup
import os 
from collections import OrderedDict
from setuptools.command.install import install

# https://stackoverflow.com/a/16609054
class Download(install):

    def nltk_download(self):
        import nltk
        nltk.downloader.download('maxent_ne_chunker')
        nltk.downloader.download('words')
        nltk.downloader.download('treebank')
        nltk.downloader.download('maxent_treebank_pos_tagger')
        nltk.downloader.download('punkt')
        # since 2020-09
        nltk.downloader.download('averaged_perceptron_tagger')

    def gunzip(self, source_filepath, dest_filepath, block_size=65536):
        import gzip
        with gzip.open(source_filepath, 'rb') as s_file, \
                open(dest_filepath, 'wb') as d_file:
            while True:
                block = s_file.read(block_size)
                if not block:
                    break
                else:
                    d_file.write(block)

    def db_download(self):
        import urllib.request
        import gzip
        from pathlib import Path
        import os

        urllib.request.urlretrieve('https://github.com/somnathrakshit/geograpy3/wiki/data/locations.db.gz', 'locations.db.gz')
        urllib.request.urlretrieve('https://github.com/somnathrakshit/geograpy3/wiki/data/regions.tgz', 'regions.tgz')
        self.gunzip("locations.db.gz", f"{str(Path(Path.home(), '.geograpy3'))}")


    def run(self):
        install.run(self)
        self.nltk_download()
        self.db_download()
        
try:
    long_description = ""
    with open('README.md', encoding='utf-8') as f:
        long_description = f.read()

except:
    print('Curr dir:', os.getcwd())
    long_description = open('../../README.md').read()

setup(name='geograpy3',
      version='0.2.3',
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
            'Programming Language :: Python :: 3.10'
      ],
      packages=['geograpy'],
      install_requires=[
        'numpy',
        'nltk',
        'newspaper3k',
        'jellyfish',
        'pylodstorage~=0.1.13',
        'sphinx-rtd-theme',
        'scikit-learn',
        'pandas'
      ],
      cmdclass={'install': Download},
      package_data={
          'geograpy': ['data/*.csv'],
      },
      zip_safe=False)
