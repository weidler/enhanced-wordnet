#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# AUTHOR: Tonio Weidler

import subprocess as sp
from pprint import pprint
from src.Glosses import CollocationMember, CollocationHead
import re
import regex
import os
import json
import datetime
from src.functions import parse_logic_transformation, find_predicates

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

		self._gloss_order = self.glosses.keys()
		self._transformation_type = "logic"

	def transform_glosses(self, target_file=None):
		print("=== Transforming Glosses ===")
		print("building corpus...")
		gloss_corpus = self._build_gloss_corpus(self.glosses)
		print("parsing...")
		parsed_gloss_corpus = self._apply_parsing_tool(gloss_corpus)
		gloss_order_reference = "%ORDER {0}\n".format(self._gloss_order)

		if target_file:
			with open(target_file, "w") as f:
				f.write(gloss_order_reference + parsed_gloss_corpus)
			return True

		else:
			return parsed_gloss_corpus

	def read_transformed_glosses(self, filename):
		with open(filename, "r") as f:
			content = f.read()

		order = re.search("%ORDER (.*?)\n", content).group(1)
		self._gloss_order = json.loads(re.sub("'", '"', order))

		transformed_glosses = re.sub("(^%.*\n|\n\Z)", "", content)
		transformed_glosses_list = [g if g != "" else "EMPTY" for g in transformed_glosses.split("\n")]

		return self._extend_glosses_with_transformations(transformed_glosses_list)

	def _extend_glosses_with_transformations(self, transformed_gloss_strings):
		transformed_glosses = {}
		for i, gloss_key in enumerate(self._gloss_order):
			gloss = self.glosses[gloss_key]
			gloss_transformation_string = transformed_gloss_strings[i]

			if gloss_transformation_string != "EMPTY":
				transformed_glosses[gloss_key] = gloss.gloss_to_transformed_gloss(gloss_transformation_string, self._parse_transformation(gloss_key, gloss_transformation_string))

		return transformed_glosses

	def _parse_transformation(self, gloss_key, transformed_gloss):
		output = {}
		gloss = self.glosses[gloss_key]

		# collect all entities and events
		variables = re.findall(r"([#∃]+)([a-z\']+)\.?", transformed_gloss)
		# parse the transformation
		parsed_logic_transformation = parse_logic_transformation(transformed_gloss)

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
				"parsed_transformation": parsed_logic_transformation
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
		disambiguated_variable_predicates = []
		gloss_token_stack = gloss.tokens.copy()

		# TODO far from perfect, too much UNKNOWN
		for i, pred in enumerate(variable_predicates):
			predicate_sense = "UNKNOWN"
			for token_id in sorted(gloss_token_stack.keys()):
				token = gloss.tokens[token_id]
				if pred.lower() == token.lemma_string.lower() or (type(token) == CollocationHead and pred.lower() == token.lemma_string.lower().split("_")[0]):
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
					break

			disambiguated_variable_predicates.append((pred, predicate_sense))

		return disambiguated_variable_predicates

	def _apply_parsing_tool(self, gloss_corpus):
		with open("gloss_corpus.tmp", "w") as f:
			f.write(gloss_corpus)

		try:
			parser_output = sp.check_output("java -Xmx2g -jar src/tools/easysrl/easysrl_fixed.jar --model src/tools/easysrl/model/ --maxLength 150 --outputFormat {0} --inputFile gloss_corpus.tmp 2>{1}".format(self._transformation_type, self._logfile+".parser_log"), shell=True)
		except sp.CalledProcessError as e:
			return e.output

		os.remove("gloss_corpus.tmp")

		return parser_output

	def _build_gloss_corpus(self, glosses, ignore_parenthesis_content=True):
		gloss_corpus = ""

		#TODO there are still some glosses that produce strange transformations with unmatching parethesis
		#TODO honestly i think i sould trash all content in parenthesis
		#TODO maybe its smarter to construct from tokens? allows combination of collocations...
		#TODO it could be better to use more than one sentences per gloss if they are seperated by ";" as otherwise its near to impossible to determine the main entity of the sentences following any ;
		for gloss_key in self._gloss_order:
			gloss = self.glosses[gloss_key]
			gloss_text = re.sub(r"[.,;:?!]", " \g<0> ", gloss.gloss_desc)
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

		with open("gloss_corpus.txt", "w") as f:
			f.write(gloss_corpus)

		return gloss_corpus

	def _log_error(self, message, gloss):
		with open(self._logfile, "a") as f:
			f.write("{0}\n\t\t{1}\n".format(message, gloss))
