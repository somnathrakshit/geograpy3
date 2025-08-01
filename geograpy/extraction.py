#!/usr/bin/env python3
# geograpy-nltk converted to python script 2024-03-29
# using Extractor as the single point of truth since 2025-07-31
import re
import nltk
from newspaper import Article
from geograpy.labels import Labels


class Extractor(object):
    """
    Extract geo context for text or from url
    """
    def __init__(self, text=None, url=None, debug=False):
        """
        Constructor
        Args:
            text(string): the text to analyze
            url(string): the url to read the text to analyze from
            debug(boolean): if True show debug information
        """
        if not text and not url:
            raise Exception("text or url is required")
        self.debug = debug
        self.text = text
        self.url = url
        self.places = []
        Extractor.provide_nltk_packages()

    @staticmethod
    def provide_nltk_packages(quiet:bool=True):
        """
        Download required NLTK packages if not available
        """
        nltk_packages = [
            "maxent_ne_chunker",
            "maxent_ne_chunker_tab", # Updated 2025-07
            "words",
            "treebank",
            "punkt",
            "punkt_tab", # Updated 2025-07
            "averaged_perceptron_tagger_eng",  # Updated: language-specific
        ]

        for nltk_package in nltk_packages:
            try:
                nltk.data.find(nltk_package)
            except LookupError:
                nltk.download(nltk_package, quiet=quiet)

    def set_text(self):
        """
        Setter for text
        """
        if not self.text and self.url:
            a = Article(self.url)
            a.download()
            a.parse()
            self.text = a.text

    def split(self, delimiter=r","):
        """
        simpler regular expression splitter with not entity check
        hat tip: https://stackoverflow.com/a/1059601/1497139
        """
        self.set_text()
        self.places = re.split(delimiter, self.text)

    def find_geoEntities(self):
        """
        Find geographic entities
        Returns:
            list:
                List of places
        """
        self.find_entities(Labels.geo)
        return self.places

    def find_entities(self, labels=Labels.default):
        """
        Find entities with the given labels set self.places and returns it
        Args:
            labels:
                Labels: The labels to filter
        Returns:
            list:
                List of places
        """
        self.set_text()
        text = nltk.word_tokenize(self.text)
        nes = nltk.ne_chunk(nltk.pos_tag(text))
        for ne in nes:
            if type(ne) is nltk.tree.Tree:
                nelabel = ne.label()
                if nelabel in labels:
                    leaves = ne.leaves()
                    if self.debug:
                        print(leaves)
                    self.places.append(" ".join([i[0] for i in leaves]))
        return self.places

def main():
    """Download essential NLTK datasets"""
    Extractor.provide_nltk_packages(quiet=False)

if __name__ == "__main__":
    main()
