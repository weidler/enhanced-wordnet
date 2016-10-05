#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# AUTHOR: Tonio Weidler

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), "../"))

from src.glosses.Glosses import LogicallyTransformedGloss
from src.functions import get_ss_type_from_sense_key, add_key, get_sk_main_variable, find_predicates
import re
from pprint import pprint

class RelationExtractor(object):
	"""
	Relation Dict Reference:
		{
			noun_key: {
				functionality: [verb_keys, ...],
				application: [verb_keys, ...],

				specification: [(hypernym_noun_key, adj_key), ...],
				attributes: [adj_key, ...]
			}

			verb_key: {
				locational_spec: [noun_key, ...],
				manner_spec: [adj_key, ...],
				temporal_spec: [???],
				be: [adjective]
			}
		}
	"""

	def __init__(self, glosses):
		self.__dict__.update(locals())
		del self.__dict__["self"]

		untransformed_glosses = [g for g in self.glosses if type(self.glosses[g]) != LogicallyTransformedGloss]
		if untransformed_glosses:
			raise Exception("Please transform the Glosses first! There are {0} glosses in this list that are not transformed!".format(len(untransformed_glosses)))
		self.extracted_relations = {}

	def extract_relations(self):
		print("=== Extract Relations ===")
		glosses = self.glosses.copy()
		extracted_relations = {}

		# travers through all those glosses and let the extraction begin!
		for gloss_key in glosses:
			gloss = glosses[gloss_key]
			gloss_entity_dict = gloss.transformed_gloss_entities
			parsed_gloss_transformation = gloss.transformed_gloss_parsed
			ss_type = gloss.pos

			gloss_relations = {}

			# extract according to the ss type of the glosses synset
			# noun relations
			if ss_type == "noun":
				main_entity_symbol = self._find_main_entity(gloss_entity_dict)
				if not main_entity_symbol:
					continue

				# relation "specification" / "attributes"
				attributes, hyperonym = self._extract_noun_specification_and_attributes(main_entity_symbol, gloss_entity_dict, parsed_gloss_transformation)

				if attributes:
					add_key("attributes", gloss_relations, value=[])
					gloss_relations["attributes"].extend([a[1] for a in attributes])

				if hyperonym and attributes:
					add_key("specifications", gloss_relations, value=[])
					gloss_relations["specifications"].extend([(hyperonym[1], a[1]) for a in attributes])

				# relation application
				applications = self._extract_noun_application(main_entity_symbol, gloss_entity_dict, parsed_gloss_transformation)

				if applications:
					add_key("application", gloss_relations, value=[])
					gloss_relations["application"].extend([f[1] for f in applications])

				# relation functionality
				functionalities = self._extract_noun_functionality(main_entity_symbol, gloss_entity_dict, parsed_gloss_transformation)

				if functionalities:
					add_key("functionality", gloss_relations, value=[])
					gloss_relations["functionality"].extend([f[1] for f in functionalities])

			# verb relations
			elif ss_type == "verb":
				main_event_symbol = self._find_main_event(gloss_entity_dict)

				if not main_event_symbol:
					continue

				# verb specifications
				specifications = self._extract_verb_specifications(main_event_symbol, gloss_entity_dict, parsed_gloss_transformation)

				for spec_type in specifications:
					if spec_type[0]:
						gloss_relations["{0}_spec".format(spec_type[1])] = set([sense[1] for sense in spec_type[0]])

			elif ss_type == "adj":
				pass  # not implemented yet
			elif ss_type == "adv":
				pass  # not implemented yet

			if gloss_relations:
				extracted_relations[gloss_key] = gloss_relations

		print("...finished")
		return extracted_relations

	def get_extracted_relations_stats(self, relations):
		total_glosses_count = len(self.glosses)
		glosses_with_relations_count = len(relations)

		gloss_ss_types = [g[0] for g in list(self.glosses.keys())]
		total_nouns = gloss_ss_types.count("n")
		total_verbs = gloss_ss_types.count("v")

		noun_relations = ["attributes", "specifications", "application", "functionality"]
		verb_relations = ["locational_spec", "manner_spec", "temporal_spec", "be"]

		print("From a total of {0} glosses of which are\n\t{1} nouns and\n\t{2} verbs\nrelations from {3} glosses where extracted,\nwhich where found as follows for their ss type:\n".format(
					total_glosses_count,
					total_nouns,
					total_verbs,
					glosses_with_relations_count
		))

		for ss_type_relations, count in zip([noun_relations, verb_relations], [total_nouns, total_verbs]):
			for r in ss_type_relations:
				r_count = 0
				for g_key in relations:
					g = relations[g_key]
					if r in list(g.keys()):
						r_count += 1
				print("{0}: {1} ({2}%)".format(r, r_count, round(r_count/float(count)*100, 2)))


	def _extract_noun_functionality(self, main_entity_symbol, gloss_entity_dict, parsed_gloss_transformation):
		pass

	def _extract_noun_application(self, main_entity_symbol, gloss_entity_dict, parsed_gloss_transformation):
		applications = []

		heuristik_1 = True
		heuristik_2 = True

		# HEURISTIK I
		# NOUN ... used ... (to) VERB
		# e.g. a spoon used to eat soup
		# go through all variables of the gloss
		if heuristik_1:
			for variable in gloss_entity_dict:
				variable_dict = gloss_entity_dict[variable]
				variable_predicates_lemmas = [l[0] for l in variable_dict["predicates"]]
				# check if the variable is an event with the predicate "use"
				if "use" in variable_predicates_lemmas and variable_dict["type"] == "event":
					# check if the needed arguments of used are existent
					if "ARG1" in variable_dict["arguments"] and "ARG2" in variable_dict["arguments"]:
						# go through all argument pairs and check them
						for i, arg_1 in enumerate(variable_dict["arguments"]["ARG1"]):
							if i < len(variable_dict["arguments"]["ARG2"]):
								arg_2 = variable_dict["arguments"]["ARG2"][i][0]
								arg_1 = arg_1[0]

								# TODO implement OR handling better
								if isinstance(arg_1, tuple):
									if arg_1[0] == "sk":
										arg_1 = get_sk_main_variable(arg_1)
									elif arg_1[0] == "OR":
										if not arg_1[1][0] == "sk": continue
										arg_1 = get_sk_main_variable(arg_1[1][0])
									else:
										print("WHAT")
								if isinstance(arg_2, tuple):
									if arg_2[0] == "sk":
										arg_2 = get_sk_main_variable(arg_2)
									elif arg_2[0] == "OR":
										if not arg_2[1][0] == "sk": continue
										arg_2 = get_sk_main_variable(arg_2[1][0])
									else:
										print("WHAT")

								if arg_2 not in gloss_entity_dict: continue
								arg_2_dict = gloss_entity_dict[arg_2]
								if arg_1 == main_entity_symbol and arg_2_dict["type"] == "event":  #TODO maybe not check by event but by contained predicates
									for predicate in arg_2_dict["predicates"]:
										if get_ss_type_from_sense_key(predicate[1]) == "v":
											applications.append(predicate)

		# HEURISTIK II
		# NOUN ... for VERB_GERUND
		# e.g a whip for controling horses
		if heuristik_2:
			# check if the main entity has arguments
			if "ARG" in gloss_entity_dict[main_entity_symbol]["arguments"]:
				main_entity_args = gloss_entity_dict[main_entity_symbol]["arguments"]["ARG"]
				# go thorough all arguments of the main entity and check them for the desired structure
				for main_entity_arg in main_entity_args:
					main_entity_arg = main_entity_arg[0]
					if not isinstance(main_entity_arg, tuple): continue

					# in case there s an OR structure, create lists we can cycle through
					possibilities = []
					if main_entity_arg[0] == "OR":
						for coordinated_arg in main_entity_arg[1]:
							if coordinated_arg[0] == 'sk':
								possibilities.append(coordinated_arg[1])
					elif main_entity_arg[0] == "sk":
						possibilities.append(main_entity_arg[1])

					# go through all possible sks
					for sk in possibilities:
						sk_existential_event = re.search(r"∃(e'*)", sk[0][0])
						if sk_existential_event:
							sk_application_event = sk_existential_event.group(1)
							applications.extend([sense for sense in gloss_entity_dict[sk_application_event]["predicates"] if sense[1] != "UNKNOWN"])

		# HEURISTIK III
		#

		return applications


	def _extract_noun_specification_and_attributes(self, main_entity_symbol, gloss_entity_dict, parsed_gloss_transformation):
		main_entity = gloss_entity_dict[main_entity_symbol]
		main_entity_predicates = main_entity["predicates"]
		hyperonym = None
		attributes = []
		for predicate in main_entity_predicates:  # TODO maybe i can even use UNKNOWNs
			if predicate[1] != "UNKNOWN" and predicate[1]:  # second condition checks if not None
				predicate_ss_type = get_ss_type_from_sense_key(predicate[1])
				if not predicate_ss_type:
					continue
				if predicate_ss_type == "n":
					hyperonym = predicate
				elif predicate_ss_type in ["a", "r", "s"]:
					attributes.append(predicate)

		return (attributes, hyperonym)

	def _extract_verb_specifications(self, main_event_symbol, gloss_entity_dict, parsed_gloss_transformation):
		locational = []
		manner = []
		temporal = []

		types = [locational, manner, temporal]
		pred_regs = ["LOC", "MNR", "TMP"]
		names = ["locational", "manner", "temporal"]

		for spec_type_list, reg in zip(types, pred_regs):
			for loc in find_predicates(parsed_gloss_transformation, reg):
				if loc[1][-1] == main_event_symbol:
					possibilities = []
					if loc[1][0][0] == "OR":
						for coord in loc[1][0][1]:
							if coord[0] == "sk":
								possibilities.append(coord)
					elif loc[1][0][0] == "sk":
						possibilities.append(loc[1][0])

					for sk in possibilities:
						spec_type_list.extend([sense for sense in gloss_entity_dict[get_sk_main_variable(sk)]["predicates"] if get_ss_type_from_sense_key(sense[1]) in ["a", "s", "r"]])

		return list(zip(types, names))


	def _find_main_entity(self, gloss_entity_dict):
		#TODO is there a smarter way?
		if "x" in gloss_entity_dict:
			return "x"
		else:
			return None

	def _find_main_event(self, gloss_entity_dict):
		#TODO is there a smarter way?
		if "e" in gloss_entity_dict:
			return "e"
		else:
			return None
