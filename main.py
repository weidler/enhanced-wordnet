#!/usr/bin/env python
# -*- coding: utf-8 -*-
# author: Tonio Weidler

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), "."))

from pprint import pprint
from src.WordnetInterface import WordNet
from src.glosses.GlossWSD import GlossDisambiguator
from src.glosses.GlossTransformation import GlossTransformer
from src.RelationExtractor import RelationExtractor
import pickle

# Settings
new_disambiguation = False
new_logic_transformation = False

use_test_gloss_portion = True
test_gloss_portion = 117659
file_extension = "_dev_" + str(test_gloss_portion)

show_detailed_output = False

# you cant create new disambiguations and use old logic parsings, as the portion of the glosses may differ in its glosses it contains
if new_disambiguation and not new_logic_transformation:
	print("Setting new_logic_transformation to 'True' - you can't initiate a use a new disambiguation with an old logical traosformation")
	new_logic_transformation = True

# initialize
wn = WordNet("data/wordnet_database/", "src/pointers/noun_pointers.txt", "src/pointers/adj_pointers.txt", "src/pointers/verb_pointers.txt", "src/pointers/adv_pointers.txt")
glosses = wn.collect_glosses()

if use_test_gloss_portion:
	glosses = {key: glosses[key] for key in list(glosses.keys())[:test_gloss_portion]}

# for some reason there are a few glosses that crash EasySRL, they are excluded here
excluded_synsets = ["n13515353", "n00658946", "n06505517", "n07061677"]
for excl in excluded_synsets:
	if excl in glosses:
		del glosses[excl]

# disambiguating the glosses or read already disambiguated glosses
if new_disambiguation:
	gd = GlossDisambiguator(glosses, ["data/wordnet_glosstags/adv.xml", "data/wordnet_glosstags/verb.xml", "data/wordnet_glosstags/noun.xml", "data/wordnet_glosstags/adj.xml"], wn)
	disambiguated_glosses = gd.disambiguate_glosses()

	print("...writing glosses")
	with open("extracted_data/glosses_disambiguated{0}.txt".format(file_extension), "wb") as f:
		pickle.dump(disambiguated_glosses, f, protocol=2)  # protocol ensures python 2 compatibility
else:
	try:
		print("...pickling Glosses")
		with open("extracted_data/glosses_disambiguated{0}.txt".format(file_extension), "rb") as f:
			disambiguated_glosses = pickle.load(f)
		print("...finished pickling")
	except IOError as io:
		raise IOError("You need to disambiguate this variant first!")

# TRANSFORMATION (alle Glossen dauern etwa 46 min)
gt = GlossTransformer(disambiguated_glosses)
if new_logic_transformation:
	gt.transform_glosses(target_file="extracted_data/transformations{0}.txt".format(file_extension))
transformed_glosses = gt.read_transformed_glosses("extracted_data/transformations{0}.txt".format(file_extension))

if show_detailed_output:
	print("\n\nDETAILED OUTPUT GLOSS TRANSFORMATIONS & PARSINGS")
	for test_gloss in transformed_glosses:
		print("\n-----------------------------------------------------------------------\n")
		print(transformed_glosses[test_gloss])
		print("")
		print(transformed_glosses[test_gloss].tokens)
		print("\n")
		pprint(transformed_glosses[test_gloss].transformed_gloss_parsed)
		print("")
		pprint(transformed_glosses[test_gloss].transformed_gloss_entities)

	print("\n\n-----------------------------------------------------------------------\n\n")

re = RelationExtractor(transformed_glosses)
relations = re.extract_relations()
if show_detailed_output: pprint(relations)
re.get_extracted_relations_stats(relations)

with open("extracted_data/relations{0}_2.rel".format(file_extension), "wb") as f:
	pickle.dump(relations, f, protocol=2)

print("\n\nDone.")
