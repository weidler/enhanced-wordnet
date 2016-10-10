EhWoN: Enhanced WordNet - Extracting interclass relations from WordNets Glosses
===============================================================================

This README explains the basic structure of the system and how to use it. More detailled explanations are found in the report. The Code is documented with docstrings.

## Requirements

EhWoN runs on `python3` but should be executable on `python2.7+` too.

EhWoN requires nltk for lemmatization and some wordnet related actions

	pip install nltk

For the evaluation of the relations, the coreference resolution framework **cort** is required

	pip install cort

pip will install any missing dependencies for those packages.

## Structure

The project is structured into the following tree of directories:

* **data/** contains the wordnet database, the glosstag files and the conll files for evaluation
	* **connl-2012/** contains the combined conll files for development, training and testing, each as auto and gold version
	* **wordnet_database/** contains the database files of WordNet 3.0
	* **wordnet_glosstags/** contains the glosstag files from the "Princeton Annotated Gloss Corpus"
* **docs/** contains several textfiles for lookups and the documentation
* **extracted_data/** contains backups of the disambiguation and transformation process for quick loads as well as the extracted `.rel` files containing the extracted relations
* **log/** is where any log files are stored
* **models/** the evaluation script stores its models here
* **src/** contains the heart of the system, all source files and tools are located here
	* **coref/** contains all cource files concerned with the evaluation of the relations using cort
	* **glosses/** contains source files for representing and processing the glosses
	* **pointers/** contains lookup files for the WordNetInterface with pointers and their relation names
	* **tools/** contains any third-party systems
