EhWoN: Enhanced WordNet - Extracting interclass relations from WordNets Glosses
===============================================================================

This README explains the basic structure of the system and how to use it. More detailled explanations are found in the report. The Code is documented with docstrings. This copy of the project is most likely INCOMPLETE as important parts are missing due to size/licenses. YOu may either download/create them
yourself or received an archive that you can simply extract into this project.

**A word about path insertion**  
I really prefer to sort my source files in different folders, but python for some reason makes it very inconveniant to import files
from directories that are in directories above the current file. Therefore I added a short code snippet into each file that adds the project
folders path to the PYTHONPATH variable. That then allows me to very convenintly import any file in the project. Though this works for me it is
somewhat experimental and there seem to be issues with updating .pyc files. If something doesnt work a good starting point may be deleting the snippet
everywhere and permanently adding the project path to the PYTHONPATH variable.

## Requirements

EhWoN runs on `python3` but should be executable on `python2.7+` too.

EhWoN requires nltk for lemmatization and some wordnet related actions

	pip install nltk

For the evaluation of the relations, the coreference resolution framework **cort** is required

	pip install cort

`pip` will install any missing dependencies for those packages.  
Don't forget that you may have to use `pip3` in case you are using python3+ and have multiple python versions installed!

### Missing in the GitHub version

The following tools and data is missing due to Licesne/filesize. Path structure is requiered!

**src/tools/easysrl/**  
Download here: https://github.com/mikelewis0/EasySRL  
**src/tools/reference-coreference-scorers-master/**  
Download here: https://github.com/conll/reference-coreference-scorers  

**data/wordnet_database/**  
	1. goto https://wordnet.princeton.edu/wordnet/download/current-version/  
	2. choose the download under *WordNet 3.0 for UNIX-like systems (including: Linux, Mac OS X, Solaris)* **Download just database files**  
	3. extract the content into the directory named as above, a *sense.[WORDCLASS]* and *data.[WORDCLASS]* for each of the four word classes and an *index.sense* file is REQUIRED!  
**data/wordnet_glosstags/**  
Download from http://wordnet.princeton.edu/glosstag.shtml and extract all 4 .xml files to the folder mentioned above  
**data/conll-2012/**  
You need the following combined corpus files:  

	dev.auto, dev.gold
	train.auto, train.gold
	test.auto, test.gold

Combine them from OntoNotes/Conll or any other conll format files. You may modify and use the script *src/coref/conll_corpus_combiner.py*  to do so.

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

## Usage

I provide two main scripts to easily use the project

***main.py***  
This wrapper/main file combines the whole disambiguation/transformation/extraction process based on some options.

***evaluate.sh***  
A command line script to manage the cort based evaluation process. Usage as follows:

	bash evaluate.sh ACTION [OPTIONS]

		ACTION		one of the following actions are possible and required:
						train	only train a model
						test	only test a model (create a prediction)
						score	only score a prediction
						all		do all of the above consecutively
		OPTIONS		options concerning the files used
			-t		training corpus name, one of train, dev or test
			-p		test corpus name, one of train, dev or test
			-f 		feature list name, one of baseline, ehwon
