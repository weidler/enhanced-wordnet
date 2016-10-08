#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# AUTHOR: Tonio Weidler

"""General functions used by multiple modules of the system."""

import re

def get_ss_type_from_sense_key(sense_key):
	"""Extract the ss type (n/v/a/r/s) of a wordnet sense key.

	Returns:
		(string):	the ss type as one char string
	"""
	if sense_key in ["purposefully_ignored%0:00:00::", "UNKNOWN", None]:
			return False
	return {1: "n", 2: "v", 3: "a", 4: "r", 5: "s"}[int(sense_key.split("%")[1].split(":")[0])]

def add_key(key, dictionary, value={}):
	"""Add a key to a dict if its not already part of it."""
	if key not in dictionary:
		dictionary[key] = value

def get_wordnet_pos(treebank_tag):

    if treebank_tag.startswith('J'):
        return "a"
    elif treebank_tag.startswith('V'):
        return "v"
    elif treebank_tag.startswith('N'):
        return "n"
    elif treebank_tag.startswith('R'):
        return "r"
    else:
        return ''

def is_noun(pos):
	if get_wordnet_pos(pos) == "n":
		return True
	return False

def is_verb(pos):
	if get_wordnet_pos(pos) == "n":
		return True
	return False

def is_adjective(pos):
	if get_wordnet_pos(pos) == "a" or get_wordnet_pos(pos) == "s":
		return True
	return False

def is_adverb(pos):
	if get_wordnet_pos(pos) == "r":
		return True
	return False

def find_predicates(parsed_transformation, arg_regex):
	"""Find all Predicate-Argument Structures in the prased transformation where the predicate matches the regex."""
	predicates = []
	for element in parsed_transformation:
		if isinstance(element, tuple):
			if isinstance(element[0], str):
				if re.match(arg_regex, element[0]):
					predicates.append(element)
			if isinstance(element[1], list):
				predicates.extend(find_predicates(element[1], arg_regex))
		elif isinstance(element, list):
			predicates.extend(find_predicates(element, arg_regex))

	return predicates

def get_sk_main_variable(parsed_transformation_sk):
	if not isinstance(parsed_transformation_sk, tuple):
		raise TypeError("get_sk_main_variable() can only be applied on skolem forms of a parsed transformation (tuple)")
	if parsed_transformation_sk[0] != "sk":
		raise TypeError("get_sk_main_variable() can only be applied on skolem forms")

	return re.search(r"[#∃]([a-z])\'*\.", parsed_transformation_sk[1][0][0]).group(1)

if __name__ == "__main__":
	parsed = ('sk', [('#x.', [('fungus', ['x']), ('ARG', [('sk', [('#y.', [('family', ['y']), ('helvellacea', ['y'])])]), 'x'])])])
	print(get_sk_main_variable(parsed))
