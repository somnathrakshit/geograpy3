import nltk
from newspaper import Article
from geograpy.labels import Labels

class Extractor(object):
    '''
    extract geo context for text or from url
    '''
    def __init__(self, text=None, url=None):
        '''
        constructor
        Args:
            text(string): the text to analyze
            url(string): the url to read the text to analyze from
            
        '''
        if not text and not url:
            raise Exception('text or url is required')

        self.text = text
        self.url = url
        self.places = []

    def set_text(self):
        '''
        setter for text
        '''
        if not self.text and self.url:
            a = Article(self.url)
            a.download()
            a.parse()
            self.text = a.text
            
    def find_geoEntities(self):
        '''
        find geographic entities
        
        Returns:
            list: of places
        '''
        self.find_entities(Labels.geo)
        return self.places

    def find_entities(self,labels=Labels.default):
        '''
        find entities with the given labels set self.places and returns it
        Args:
            labels(Labels): the labels to filter
        Returns:
            list: of places
        '''
        self.set_text()

        text = nltk.word_tokenize(self.text)
        nes = nltk.ne_chunk(nltk.pos_tag(text))

        for ne in nes:
            if type(ne) is nltk.tree.Tree:
                if (ne.label() in labels):
                    self.places.append(u' '.join([i[0] for i in ne.leaves()]))
        return self.places