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

def parse_logic_transformation(transformation):
	"""Parse a logic transformation into a python-readable representation of lists and tuples."""
	# TODO implement such coordinations as (...|...)
	predicate_argument_pattern = re.compile(r"([^()\[\],&|{}]+)|\s*([|,()\[\]{}&])\s*")
	if transformation.count("(") != transformation.count(")"):
		raise SyntaxError("Unmatching amount of brackets\n{0}!".format(transformation))

	args = []
	current_element = None  # may be a single element or a function with its arguments
	state = 0  # 0 -> before element, 1 -> after element, 2 -> after closing bracket
	stack = []  # remembers the last arg/current_element before the current level was entered
	coordination = False  # tracks, whether the current element is a coordination

	for match in predicate_argument_pattern.finditer(transformation):
		# handle predicates
		if match.group(1):
			if state == 1: raise RuntimeError("Regex failed; Expected argument structure for last element at {0}\n{1}!".format(match.start(), transformation))
			if state == 2: print("Missing control symbol for argument listing at {0}\n{1}!".format(match.start(), transformation))

			current_element = match.group(1)
			state = 1

		# handle control symbols
		elif match.group(2) in "([{":
			# TODO handle quantifier skopus of []
			coordination = False

			if match.group(2) == "{":
				coordination = True

			if coordination:
				current_element = "OR"

			stack.append((args, current_element, coordination))  # a new argument structure begins so remember the old level
			current_element = None
			state = 0
			args = []

		elif match.group(2) in ")]}":
			if match.group(2) == "}":
				coordination = False

			# if there is nothing in the stack, then there was no opening bracket for this closing bracket
			if not stack: print("unmatched closing bracket at {0}\n{1}".format(match.start(), transformation))
			# if the last element was either an single element or a predicate+argument than add this to the args of the current level
			if state != 0: args.append(current_element)

			# then close the level by using the higher level current element (which should be a predicate) and the current args as new current element
			# and setting the current args equal to the higher level args
			# this means: go one level higher and add this level to the higher level as an argument
			predicate_args = args
			args, current_element, coordination = stack.pop()
			current_element = (current_element, predicate_args)

			state = 2

		elif match.group(2) in ",&|":
			if state != 0: args.append(current_element)
			current_element = None
			state = 0

		# elif match.group(2) == "|":
		# 	if not coordination: raise SyntaxError("OR element in non-coordination at {0}\n{1}".format(match.start(), transformation))
		# 	if state != 0: args.append(current_element)
		# 	current_element = None
		# 	state = 0

	if state != 0: args.append(current_element)

	return args

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
	from pprint import pprint
	import timeit
	import regex

	with open("transformations_100.txt", "r") as f:
		corpus = f.read().split("\n")[1:]

	test_string = "sk(#x.(phrase(x)&∃e[(use(e)&ARG1(x,e)&∃e'[∃y[(say(e')&ARG0(y,e')&∃e''[(examine(e'')&ARG1(sk(#z.publication(z)),e'')&contain(e'')&ARG0(sk(#z.publication(z)),e'')&∃e'''[(offensive(e''')&ARG(sk(#u.nothing(u)),e''')&to(sk(#v.church(v)),e''')&ARG1(e''',e''))]&ARG1(sk(#u.nothing(u)),e'')&ARG1(e'',e'))]&ARG(e',e))]]&ARG(sk(#x'.(censor(x')&ARG(sk(#y'.roman-catholic-church(y')),x')&official(x'))),e))]))"

	tic_r = timeit.default_timer()
	predicate_pattern = regex.compile(r"(\w+)(?=\(((?:[^()]*\((?2)\)|[^()])*)\))")
	predicates_with_contents = predicate_pattern.findall(test_string)
	toc_r = timeit.default_timer()

	tic_p = timeit.default_timer()
	p = parse_logic_transformation(test_string)
	preds = find_predicates(p, "[a-z]+")
	pprint(preds)
	toc_p = timeit.default_timer()

	print("Regex: {0}s\nParser: {1}s".format(toc_r - tic_r, toc_p - tic_p))

	parsed = ('sk', [('#x.', [('fungus', ['x']), ('ARG', [('sk', [('#y.', [('family', ['y']), ('helvellacea', ['y'])])]), 'x'])])])
	print(get_sk_main_variable(parsed))
