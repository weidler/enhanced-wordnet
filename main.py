#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pprint import pprint
from src.WordnetInterface import WordNet
from src.GlossWSD import GlossDisambiguator
from src.GlossTransformation import GlossTransformer
from src.RelationExtractor import RelationExtractor
import pickle

# Settings
new_disambiguation = False
use_test_gloss_portion = True
new_logic_parsing = False
file_extension = "_50000"

wn = WordNet("data/wordnet_database/", "src/noun_pointers.txt", "src/adj_pointers.txt", "src/verb_pointers.txt", "src/adv_pointers.txt")
glosses = wn.collect_glosses()

if use_test_gloss_portion:
	glosses = {key: glosses[key] for key in glosses.keys()[:50000]}

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
	with open("glosses_disambiguated{0}.txt".format(file_extension), "w") as f:
		pickle.dump(disambiguated_glosses, f)
else:
	print("...pickling Glosses")
	with open("glosses_disambiguated{0}.txt".format(file_extension), "r") as f:
		disambiguated_glosses = pickle.load(f)
	print("...finished pickling")

# TRANSFORMATION (alle Glossen dauern etwa 46 min)
gt = GlossTransformer(disambiguated_glosses)
if new_logic_parsing:
	gt.transform_glosses(target_file="transformations{0}.txt".format(file_extension))

transformed_glosses = gt.read_transformed_glosses("transformations{0}.txt".format(file_extension))

# test_gloss = 0
# for test_gloss in transformed_glosses:
# 	print("\n\n")
# 	print(transformed_glosses[test_gloss])
# 	print(transformed_glosses[test_gloss].tokens)
# 	pprint(transformed_glosses[test_gloss].transformed_gloss_entities)

re = RelationExtractor(transformed_glosses)
relations = re.extract_relations()
# pprint(relations)
re.get_extracted_relations_stats(relations)

print("\n\nDone.")
