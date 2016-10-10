#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# AUTHOR: Tonio Weidler

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), "../../"))

import subprocess as sp
from pprint import pprint
from src.glosses.Glosses import CollocationMember, CollocationHead
import re
import regex
import json
import datetime
from src.functions import find_predicates

class GlossTransformer(object):

	def __init__(self, glosses):
		self.__dict__.update(locals())
		del self.__dict__["self"]

		log_dir = "log/"
		time = datetime.datetime.now()
		timestamp = "{0}_{1}_{2}_{3}:{4}".format(time.day, time.month, time.year, time.hour, time.minute)
		self._logfile = log_dir + "gloss_transformation_" + timestamp + ".log"
		with open(self._logfile, "w") as f:
			f.write("LOG FILE - GLOSS TRANSFORMATION\n\n")

		self._gloss_order = list(self.glosses.keys())
		self._transformation_type = "logic"

		self._mappable_predicates = 0
		self._mapped_predicates = 0

	def transform_glosses(self, target_file=None):
		print("=== Transforming Glosses ===")
		print("building corpus...")
		gloss_corpus = self._build_gloss_corpus(self.glosses)
		print("transforming...")
		parsed_gloss_corpus = self._apply_transformation_tool(gloss_corpus)
		gloss_order_reference = "%ORDER {0}\n".format(self._gloss_order)

		if target_file:
			with open(target_file, "w") as f:
				f.write(str(gloss_order_reference + parsed_gloss_corpus))
			return True

		else:
			return parsed_gloss_corpus

	def read_transformed_glosses(self, filename):
		print("=== Transforming Glosses ===")
		with open(filename, "r") as f:
			content = f.read()

		order = re.search("%ORDER (.*?)\n", content).group(1)
		self._gloss_order = json.loads(re.sub("'", '"', order))

		transformed_glosses = re.sub("(^%.*?\n|\n\Z)", "", content)
		transformed_glosses_list = [g if g != "" else "EMPTY" for g in transformed_glosses.split("\n")]

		return self._extend_glosses_with_transformations(transformed_glosses_list)

	def _extend_glosses_with_transformations(self, transformed_gloss_strings):
		print("...parsing transformations")
		transformed_glosses = {}

		self._mappable_predicates = 0
		self._mapped_predicates = 0

		for i, gloss_key in enumerate(self._gloss_order):
			gloss = self.glosses[gloss_key]
			gloss_transformation_string = transformed_gloss_strings[i]

			if gloss_transformation_string != "EMPTY":
				parsed_transformation = GlossTransformer.parse_logic_transformation(gloss_transformation_string)

				if gloss_key not in transformed_glosses:
					transformed_glosses[gloss_key] = gloss.gloss_to_transformed_gloss([gloss_transformation_string], [self._extract_entities_from_transformation(gloss_key, gloss_transformation_string, parsed_transformation)], [parsed_transformation])
				else:
					transformed_glosses[gloss_key].transformed_gloss_strings.append(gloss_transformation_string)
					transformed_glosses[gloss_key].transformed_gloss_entities.append(self._extract_entities_from_transformation(gloss_key, gloss_transformation_string, parsed_transformation))
					transformed_glosses[gloss_key].transformed_gloss_parsed.append(parsed_transformation)

		print("...of {0} predicates in the transformation {1} ({2}) could be mapped to a key.".format(self._mappable_predicates, self._mapped_predicates, round(self._mapped_predicates/float(self._mappable_predicates)*100, 2)))

		return transformed_glosses

	@staticmethod
	def parse_logic_transformation(transformation):
		"""Parse a logic transformation into a python-readable representation of lists and tuples."""
		predicate_argument_pattern = re.compile(r"([^()\[\],&|{}]+)|\s*([|,()\[\]{}&])\s*")
		if transformation.count("(") != transformation.count(")"):
			raise SyntaxError("Unmatching amount of brackets\n{0}!".format(transformation))

		args = []
		current_element = None  # may be a single element or a function with its arguments
		state = 0  # 0 -> before element, 1 -> after element, 2 -> after closing bracket, 3 -> after round opening bracket; 3 implies 0
		stack = []  # remembers the last arg/current_element before the current level was entered
		existential_skopus = False  # tracks whether an existential skopus has been opened in the last step

		for match in predicate_argument_pattern.finditer(transformation):
			# handle predicates
			if match.group(1):
				if state == 1: raise RuntimeError("Regex failed; Expected argument structure for last element at {0}\n{1}!".format(match.start(), transformation))
				if state == 2: print(("Missing control symbol for argument listing at {0}\n{1}!".format(match.start(), transformation)))

				current_element = match.group(1)
				state = 1

			# handle control symbols
			elif match.group(2) in "([{":

				if match.group(2) == "{":
					current_element = "OR"
					state = 0
				elif match.group(2) == "[":
					existential_skopus = True
					state = 0
				elif match.group(2) == "(":
					if state == 3: current_element = "OR"
					if existential_skopus:
						current_element = "EXISTENTIAL_SKOPUS"
						existential_skopus = False

					state = 3

				stack.append((args, current_element))  # a new argument structure begins so remember the old level
				current_element = None
				args = []

			elif match.group(2) in ")]}":
				# if there is nothing in the stack, then there was no opening bracket for this closing bracket
				if not stack: print(("unmatched closing bracket at {0}\n{1}".format(match.start(), transformation)))
				# if the last element was either an single element or a predicate+argument than add this to the args of the current level
				if state != 0 and state != 3: args.append(current_element)

				# then close the level by using the higher level current element (which should be a predicate) and the current args as new current element
				# and setting the current args equal to the higher level args
				# this means: go one level higher and add this level to the higher level as an argument
				predicate_args = args
				args, current_element = stack.pop()
				current_element = (current_element, predicate_args)

				state = 2

			elif match.group(2) in ",&":
				if state != 0 and state != 3: args.append(current_element)
				current_element = None
				state = 0

			elif match.group(2) == "|":
				# TODO handle this better
				if state == 0 and state == 3:
					raise SyntaxError("Found | after opening bracket at {0}\n{1}!".format(match.start(), transformation))
				args.append(current_element)
				current_element = "WRAPPER"
				state = 0

		if state != 0: args.append(current_element)

		return args


	def _extract_entities_from_transformation(self, gloss_key, transformed_gloss, parsed_logic_transformation):
		output = {}
		gloss = self.glosses[gloss_key]

		# collect all entities and events
		variables = re.findall(r"([#∃]+)([a-z\']+)\.?", transformed_gloss)

		# DEPRECATED
		# predicate_pattern = regex.compile(r"(\w+)(?=\(((?:[^()]*\((?2)\)|[^()])*)\))")
		# predicates_with_contents = predicate_pattern.findall(transformed_gloss)

		# find relevant information per variable
		for v_tuple in variables:
			v_quantifier, v = v_tuple
			# determine the variables type
			if re.match("[xyzuv]'*", v):
				variable_type = "entity"
			elif re.match("e'*", v):
				variable_type = "event"
			elif re.match("[pqr]'*", v):
				variable_type = "other"
			else:
				self._log_error("WARNING: unhandled variable symbol {0}".format(v), gloss_key)

			# get all predicates that ONLY contain the variable and therefore modify it directly
			all_predicates = find_predicates(parsed_logic_transformation, r"([#∃][a-z]\'*\.)?([a-z]+)")
			variable_predicates = set([re.search(r"([#∃][a-z]\'*\.)?([a-z]+)", predicates[0]).group(2) for predicates in all_predicates if len(predicates[1]) == 1 and v in predicates[1]])

			# map predicates with senses
			disambiguated_variable_predicates = self._map_senses_to_predicates(variable_predicates, gloss)

			# initialize the transformation parse dict with general information that all variable types need
			output[v] = {
				"type": variable_type,
				"predicates": disambiguated_variable_predicates,
				"quantifier": {"#": "lambda", "∃": "existential"}[v_quantifier],
			}

			# add special event information
			if variable_type == "entity":
				entity_arguments = [arg for arg in find_predicates(parsed_logic_transformation, "ARG") if arg[1][-1] == v]

				output[v].update({
						"arguments": {}
				})

				for arg in entity_arguments:
					# any argument needs to be a list in case a coordination implies multiple arguments at the same position
					argument = arg[1][:-1]

					# add the arguments to the output
					if arg[0] not in output[v]["arguments"]:
						output[v]["arguments"].update({arg[0]: [argument]})
					else:
						output[v]["arguments"][arg[0]].append(argument)

			if variable_type == "event":
				event_arguments = [arg for arg in find_predicates(parsed_logic_transformation, "ARG[A-Z0-9]?") if arg[1][-1] == v]

				output[v].update({
						"arguments": {}
				})

				for arg in event_arguments:
					# any argument needs to be a list in case a coordination implies multiple arguments at the same position
					argument = arg[1][:-1]

					# add the arguments to the output
					if arg[0] not in output[v]["arguments"]:
						output[v]["arguments"].update({arg[0]: [argument]})
					else:
						output[v]["arguments"][arg[0]].append(argument)


		return output

	def _map_senses_to_predicates(self, variable_predicates, gloss):
		# TODO better mapping for multiple gloss descriptions
		disambiguated_variable_predicates = []
		gloss_token_stack = gloss.tokens.copy()

		for i, pred in enumerate(variable_predicates):
			self._mappable_predicates += 1
			predicate_sense = "UNKNOWN"
			for token_id in sorted(gloss_token_stack.keys()):
				token = gloss.tokens[token_id]
				if pred.lower() in token.lemma_strings or (type(token) == CollocationHead and pred.lower() in [coll.split("_")[0] for coll in token.lemma_strings]):
					if type(token) == CollocationMember:
						for i in gloss.tokens:
							t = gloss.tokens[i]
							if type(t) == CollocationHead:
								# there are some odd cases where the member has two heads, heuristacally the first head will be taken
								if token.collocation_id[0] in t.collocation_id:
									coll_head = t
									break
						else:
							coll_head = None  # actually if this happens an error occurs

						predicate_sense = coll_head.collocation_wn_sense_key
					elif type(token) == CollocationHead:
						predicate_sense = token.collocation_wn_sense_key
					else:
						predicate_sense = token.wn_sense_key
					gloss_token_stack.pop(token_id)
					self._mapped_predicates += 1
					break

			disambiguated_variable_predicates.append((pred, predicate_sense))

		return disambiguated_variable_predicates

	def _apply_transformation_tool(self, gloss_corpus):
		with open("gloss_corpus.tmp", "w") as f:
			f.write(gloss_corpus)

		try:
			parser_output = sp.check_output("java -Xmx2g -jar src/tools/easysrl/easysrl_fixed.jar --model src/tools/easysrl/model/ --maxLength 150 --outputFormat {0} --inputFile gloss_corpus.tmp 2>{1}".format(self._transformation_type, self._logfile+".parser_log"), shell=True, universal_newlines=True)
		except sp.CalledProcessError as e:
			return e.output

		os.remove("gloss_corpus.tmp")

		return parser_output

	def _build_gloss_corpus(self, glosses, ignore_parenthesis_content=True):
		gloss_corpus = ""
		corpus_gloss_order = []  # gloss order for the corpus, including duplicate entries for glosses with multiple definitions

		for gloss_key in self._gloss_order:
			gloss = self.glosses[gloss_key]
			gloss_definitions = gloss.gloss_definitions
			for definition in gloss_definitions:
				gloss_text = re.sub(r"[.,;:?!]", " \g<0> ", definition)
				gloss_text = re.sub(r"'(s)", "\g<1>", gloss_text)
				if ignore_parenthesis_content:
					gloss_text = re.sub(r"\(.*?\)", "", gloss_text)  # TODO das isn kack regex, brauche recursive
					gloss_text = re.sub(r"[()]", "", gloss_text)
				else:
					gloss_text = re.sub(r"\(", " -LRB- ", gloss_text)
					gloss_text = re.sub(r"\)", " -RRB- ", gloss_text)

				gloss_text = re.sub(r"(\s)+", "\\1", gloss_text)

				if gloss_text != "":
					gloss_corpus += gloss_text + "\n"
				else:
					gloss_corpus += "PLACEHOLDER" + "\n"
					self._log_error("WARNING: Empty Gloss", gloss)

				corpus_gloss_order.append(gloss_key)

		# save gloss corpus to file for debugging purposes
		with open("gloss_corpus.txt", "w") as f:
			f.write(gloss_corpus)

		self._gloss_order = corpus_gloss_order
		return gloss_corpus

	def _log_error(self, message, gloss):
		with open(self._logfile, "a") as f:
			f.write("{0}\n\t\t{1}\n".format(message, gloss))

if __name__ == "__main__":
	from pprint import pprint
	import timeit
	import regex

	with open("extracted_data/transformations_100.txt", "r") as f:
		corpus = f.read().split("\n")[1:]

	test_string = "sk(#x.(phrase(x)&∃e[(use(e)&ARG1(x,e)&∃e'[∃y[(say(e')&ARG0(y,e')&∃e''[(examine(e'')&ARG1(sk(#z.publication(z)),e'')&contain(e'')&ARG0(sk(#z.publication(z)),e'')&∃e'''[(offensive(e''')&ARG(sk(#u.nothing(u)),e''')&to(sk(#v.church(v)),e''')&ARG1(e''',e''))]&ARG1(sk(#u.nothing(u)),e'')&ARG1(e'',e'))]&ARG(e',e))]]&ARG(sk(#x'.(censor(x')&ARG(sk(#y'.roman-catholic-church(y')),x')&official(x'))),e))]))"

	tic_r = timeit.default_timer()
	predicate_pattern = regex.compile(r"(\w+)(?=\(((?:[^()]*\((?2)\)|[^()])*)\))")
	predicates_with_contents = predicate_pattern.findall(test_string)
	toc_r = timeit.default_timer()

	tic_p = timeit.default_timer()
	p = GlossTransformer.parse_logic_transformation(test_string)
	preds = find_predicates(p, "[a-z]+")
	pprint(p)
	toc_p = timeit.default_timer()

	print("Regex: {0}s\nParser: {1}s".format(toc_r - tic_r, toc_p - tic_p))
