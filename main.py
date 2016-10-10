#!/usr/bin/env python3
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
file_extension = "_dev"

new_disambiguation = True
new_logic_transformation = True

use_test_gloss_portion = True
test_gloss_portion = 1000

show_detailed_output = False

if use_test_gloss_portion:
	file_extension += "_" + str(test_gloss_portion)
else:
	file_extension += "_full"

# you cant create new disambiguations and use old logic parsings, as the portion of the glosses may differ in its glosses it contains
if new_disambiguation and not new_logic_transformation:
	print("Setting new_logic_transformation to 'True' - you can't initiate a new disambiguation with an old logical transformation")
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

re = RelationExtractor(transformed_glosses)
relations = re.extract_relations()

if show_detailed_output:
	for synset_id in transformed_glosses:
		print("\n-----------------------------------------------------------------------\n")
		if synset_id in relations:
			pprint(relations[synset_id])
		else:
			print("no relations extracted...")

		print("\n\n")
		print(transformed_glosses[synset_id])
		print("\nTokens:")
		print(transformed_glosses[synset_id].tokens)
		print("\nParsed Transformation")
		pprint(transformed_glosses[synset_id].transformed_gloss_parsed)
		print("\nEntities")
		pprint(transformed_glosses[synset_id].transformed_gloss_entities)

		print("\n\n-----------------------------------------------------------------------\n\n")

re.get_extracted_relations_stats(relations)

with open("extracted_data/relations{0}.rel".format(file_extension), "wb") as f:
	pickle.dump(relations, f, protocol=2)

print("\n\nDone.")
