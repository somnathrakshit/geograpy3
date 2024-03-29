#!/usr/bin/env python3
# converted to python script 2024-03-29
import nltk
def main():
    nltk.downloader.download('maxent_ne_chunker')
    nltk.downloader.download('words')
    nltk.downloader.download('treebank')
    nltk.downloader.download('maxent_treebank_pos_tagger')
    nltk.downloader.download('punkt')
    # since 2020-09
    nltk.downloader.download('averaged_perceptron_tagger')

if __name__ == "__main__":
    main()
