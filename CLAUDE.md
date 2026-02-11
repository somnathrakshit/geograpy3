# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

geograpy3 is a Python library that extracts place names (countries, regions, cities) from text or URLs and adds geographic context to them. It uses Natural Language Processing (NLTK) for entity recognition and Wikidata-derived databases for location disambiguation.

## Development Commands

### Installation
```bash
pip install .
geograpy-nltk  # Downloads required NLTK models
```

Or use the install script:
```bash
scripts/install
```

### Testing
```bash
# Run all tests
scripts/test

# Run with unittest directly
python3 -m unittest discover

# Run a single test file
python3 -m unittest tests.test_locator

# Run a specific test
python3 -m unittest tests.test_locator.TestLocator.test_issue_86
```

### Code Formatting
```bash
scripts/blackisort  # Runs isort and black on geograpy/ and tests/
```

### Documentation
```bash
scripts/doc  # Generates Sphinx documentation in docs/source
```

## Architecture

### Two-Stage Processing Pipeline

1. **Extraction Stage** (`extraction.py`): Uses NLTK to identify potential geographic entities in text
   - `Extractor` class downloads and parses text from URLs or accepts raw text
   - Tokenizes text and applies Named Entity Recognition (NER)
   - Filters entities by label types (GPE/GSP for geographic, PERSON, ORGANIZATION for full context)
   - Returns a list of place name strings

2. **Location Stage** (`locator.py`, `places.py`): Adds geographic context and relationships
   - `PlaceContext` extends `Locator` to categorize and disambiguate place names
   - Queries SQLite database (populated from Wikidata) to match place names to cities, regions, countries
   - Disambiguates homonyms using population data and geographic relationships
   - Returns structured data with country-region-city hierarchies

### Key Classes

- **`Extractor`** - NLP-based entity extraction from text/URLs
- **`PlaceContext`** - High-level API that combines extraction and location lookup
- **`Locator`** - Singleton that manages the geographic database and location queries
- **`LocationManager`** - Extends `EntityManager` from pylodentitymanager to handle location collections
- **`Wikidata`** - Queries Wikidata SPARQL endpoint to populate/update location database
- **`City`, `Region`, `Country`** - Entity classes representing geographic locations

### Database Management

The locator uses an SQLite database (`locs.db`) populated from Wikidata:
- Database is downloaded/cached on first use via `Locator.downloadDB()`
- Contains tables: `countries`, `regions`, `cities`, `country_labels`, etc.
- Uses BallTree (scikit-learn) for efficient geographic distance calculations
- Primary keys are Wikidata QIDs (e.g., "Q90" for Paris)

### Entry Points

Main API functions in `geograpy/__init__.py`:
- `get_geoPlace_context(url=None, text=None)` - Extract geographic entities only
- `get_place_context(url=None, text=None)` - Extract all entities (geo, person, org)
- `locateCity(location)` - Directly locate a city from a string

Command-line scripts (defined in pyproject.toml):
- `geograpy` - CLI for location lookup
- `geograpy-nltk` - Downloads required NLTK packages

## Testing Notes

- All tests inherit from `Geograpy3Test` in `tests/basetest.py`
- Tests call `Locator.resetInstance()` and `locator.downloadDB()` in setUp
- Tests check `self.inCI()` to skip Wikidata queries in CI environments
- Use `debug=True` parameter to enable verbose output during development
