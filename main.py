#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pprint import pprint
from src.WordnetInterface import WordNet
from src.GlossWSD import GlossDisambiguator
from src.GlossTransformation import GlossTransformer

wn = WordNet("data/wordnet_database/", "src/noun_pointers.txt", "src/adj_pointers.txt", "src/verb_pointers.txt", "src/adv_pointers.txt")
glosses = wn.collect_glosses()

# DISAMBIGUATION
# gd = GlossDisambiguator(glosses, "data/wordnet_glosstags/adv.xml", wn)
# disambiguated_glosses = gd.disambiguate_glosses()

# TRANSFORMATION (alle Glossen dauern etwa 46 min)
gt = GlossTransformer(glosses)
print("Glosses: {0}".format(len(glosses)))
gt.transform_glosses(target_file="full_transformation.txt")
transformed_glosses = gt.read_transformed_glosses("full_transformation.txt")
print(transformed_glosses[transformed_glosses.keys()[17]])

print("\n\nDone.")
