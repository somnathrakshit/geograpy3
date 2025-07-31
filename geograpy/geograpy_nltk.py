#!/usr/bin/env python3
# converted to python script 2024-03-29
import nltk
def main():
    """Download essential NLTK datasets."""
    datasets = [
        'punkt',
        'punkt_tab', 
        'averaged_perceptron_tagger',  # replaces maxent_treebank_pos_tagger
        'maxent_ne_chunker',
        'words',
        'treebank'
    ]

    for dataset in datasets:
        nltk.download(dataset)


if __name__ == "__main__":
    main()
