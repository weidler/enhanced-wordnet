#!/usr/bin/env python
# -*- coding: utf-8 -*-
# AUTHOR: Tonio Weidler

from pprint import pprint
import xml.etree.ElementTree as ET
import re
import datetime
from Glosses import Token, CollocationHead, CollocationMember
from nltk.corpus import wordnet as wn
from itertools import product as list_product, combinations

GLOSSTAG_POS_POSSIBLE_SS_TYPES = {
	"(": [],
	")": [],
	",": [],
	".": [],
	"...": [],
	":": [],
	"CC": [],
	"CD": [1, 3],
	"DT": [],
	"FW": [3],
	"IN": [3],
	"JJ": [3],
	"JJR": [3],
	"JJS": [3],
	"MD": [2],
	"NN": [1],
	"NNP": [1],
	"NNS": [1],
	"PDT": [1, 3, 4],
	"PRP": [],
	"PRP$": [],
	"RB": [4],
	"RBR": [4],
	"RBS": [4],
	"RP": [1, 2, 3, 4, 5],  # not sure about this, mainly appears in CFs anyways
	"SYM": [1, 2, 3, 4, 5],  # not sure either
	"TO": [],
	"UH": [],
	"VB": [2],
	"VBD": [2],
	"VBG": [2],
	"VBN": [2],
	"VBP": [2],
	"VBZ": [2],
	"WDT": [3, 4],
	"WP": [],
	"WP$": [],
	"WRB": [4]
}

class GlossDisambiguator(object):

	def __init__(self, glosses, glosstag_file, reference_wordnet):
		self.__dict__.update(locals())
		del self.__dict__["self"]

		# LOGGING
		log_dir = "log/"
		time = datetime.datetime.now()
		timestamp = "{0}-{1}-{2}_{3}:{4}".format(time.day, time.month, time.year, time.hour, time.minute)
		self._invalid_key_logfile = log_dir + "invalid_keys_" + timestamp + ".log"
		with open(self._invalid_key_logfile, "w") as f:
			f.write("LOG FILE - INVALID KEYS\n\n")
		self._logged_keys = []


	def disambiguate_glosses(self):
		print("=== Disambiguating Glosses... ===")
		merged_glosses = self._merge_glosses_with_glosstag_file()
		disambiguated = self._disambiguate_merged_glosses(merged_glosses)

		return disambiguated

	### MAIN PROTECTED METHODS ###

	def _merge_glosses_with_glosstag_file(self):
		glosses = self.glosses
		tree = ET.parse(self.glosstag_file)
		root = tree.getroot()

		def resolve_wrapper_nodes(node_list):
			resolved_nodes = []
			for node in node_list:
				if node.tag in ["wf", "cf"]:
					resolved_nodes.append(node)
				if node.tag in ["qf", "mwf"]:
					resolved_nodes += resolve_wrapper_nodes(node.findall("*"))

			return resolved_nodes


		# assign glosstag file WSD to the glosses
		for synset in root:
			synset_id = synset.attrib["id"]
			if synset_id in glosses:
				gloss_def = synset.find("./gloss/[@desc='wsd']/def")
				tokens = resolve_wrapper_nodes(gloss_def.findall("*"))

				# travers through all tokens in the gloss
				for token in tokens:
					pos = token.attrib["pos"]
					token_object = None
					token_id_in_gloss = token.attrib["id"][-1]
					anno_tag = token.attrib["tag"]

					# check if its a collocation or a normal wf
					if token.tag == "wf":
						if "lemma" in token.keys():
							lemma = token.attrib["lemma"]
						elif "pos" in token.keys():
							lemma = token.attrib["pos"]

						# handle different annotation scenarios
						if anno_tag == "ignore":
							# token is not part of WN
							token_original_form = token.text
							token_wn_synset_offset = None
							token_wn_sense_key = None

						elif anno_tag == "un":
							# token is part of WN but wasnt disambiguated
							token_original_form = token.text
							token_wn_synset_offset = None
							token_wn_sense_key = None

						else:
							# token is disambiguated, Disambiguation is in id tag inside the wf tag
							disambiguation = token.find("id")

							token_original_form = disambiguation.tail
							token_wn_synset_offset = ""  # TODO
							token_wn_sense_key = disambiguation.attrib["sk"]

						token_object = Token(token_id_in_gloss, token_original_form, lemma, token_wn_synset_offset, token_wn_sense_key, anno_tag, pos)

					elif token.tag == "cf":
						token_wn_synset_offset = None
						token_wn_sense_key = None

						# handle different tyoes of collocations
						if token.find("glob") is not None:
							# cf is the collocation head and may contain a disambiguated id
							collocation_glob = token.find("glob")
							token_original_form = collocation_glob.tail
							collocation_id = token.attrib["coll"]
							lemma = token.attrib["lemma"]

							if collocation_glob.attrib["tag"] == "un":
								# cf was not disambiguated
								collocation_lemma = collocation_glob.attrib["lemma"]
								collocation_wn_sense_key = None
								collocation_tag = collocation_glob.attrib["tag"]

							elif collocation_glob.attrib["tag"] == "ignore":
								# that makes no sense
								print("IGNORED CF HEAD GLOB FOUND")
							else:
								# cf is disambiguated inside the globs id tag
								disambiguation = collocation_glob.find("id")
								collocation_lemma = disambiguation.attrib["lemma"]
								collocation_wn_sense_key = disambiguation.attrib["sk"]
								collocation_tag = collocation_glob.attrib["tag"]

							token_object = CollocationHead(token_id_in_gloss, token_original_form, lemma, token_wn_synset_offset, token_wn_sense_key, anno_tag, pos, collocation_id, collocation_lemma, collocation_wn_sense_key, collocation_tag)

						else:
							# cf is not the head of a collocation
							token_original_form = token.text
							collocation_id = token.attrib["coll"]
							lemma = token.attrib["lemma"]

							token_object = CollocationMember(token_id_in_gloss, token_original_form, lemma, token_wn_synset_offset, token_wn_sense_key, anno_tag, pos, collocation_id)

					else:
						print("WARNING: unknown token tag!")


					glosses[synset_id].tokens[token_id_in_gloss] = token_object

		return glosses

	def _disambiguate_merged_glosses(self, merged_glosses):

		processed_glosses = {}
		total_glosses = len(merged_glosses)
		current_gloss = 0
		disambiguated_glosses_count = 0

		# go over all glosses and disambiguate them if possible
		for gloss_key in merged_glosses:
			current_gloss += 1
			gloss = merged_glosses[gloss_key]
			taggable_tokens = []
			tagged_tokens = []

			# for each token inside the gloss determine if the token is already disambiguated, needs to be disambiguated or isnt part of WordNet anyways
			for token_index in gloss.tokens:
				token = gloss.tokens[token_index]
				tokens_wn_ss_types = map(int, re.findall("[0-9]+", token.lemma))
				# tokens that are tagged as "man" or "auto" are already disambiguated
				if token.tag in ["man", "auto"]:
					tagged_tokens.append(token)
				# if a token is tagged as "un" it is not yet annotated, but possibly should be; if the lemma contains entries of the type "LEMMA%SS_TYPE" and the POS if the
				# word matches one of the lemma-ss_types it needs to be/can be disambiguated
				elif token.tag == "un" and re.match("([a-z]+%[0-9]\|?)+", token.lemma) and not set(GLOSSTAG_POS_POSSIBLE_SS_TYPES[token.pos]).isdisjoint(set(tokens_wn_ss_types)):
					taggable_tokens.append(token)

			# if there are no remaining taggable tokens, then proceed with the next gloss
			if len(taggable_tokens) == 0:
				continue
			disambiguated_glosses_count += 1

			## DISAMBUGATION PROCEDURE ##
			print("\tat gloss {0} of {1}".format(current_gloss, total_glosses))
			print("\t\t...disambiguating {0} words in gloss {1}".format(len(taggable_tokens), gloss_key))
			# disambiguated_gloss = self._disambiguate_gloss_with_path_similarity(gloss, taggable_tokens, tagged_tokens)
			disambiguated_gloss = self._disambiguate_gloss_by_most_frequent_sense(gloss, taggable_tokens, tagged_tokens)
			# finished, append to output
			processed_glosses[gloss_key] = disambiguated_gloss

		print("\tDISAMBIGUATED {0} GLOSSES".format(disambiguated_glosses_count))
		return processed_glosses

	## Disambiguation Methods ##

	def _disambiguate_gloss_by_most_frequent_sense(self, gloss, taggable_tokens, tagged_tokens):

		disambiguated_gloss = gloss

		for undisambiguated_token in taggable_tokens:
			possible_senses = self._get_possible_wn_senses_for_token(undisambiguated_token)
			most_frequent_sense = max(possible_senses, key=lambda s: self.reference_wordnet.wordnet["sense_index"][str(s)]["tag_cnt"])

			token_index = undisambiguated_token.id

			if undisambiguated_token.wn_sense_key is None and undisambiguated_token.wn_synset_offset is None:
				disambiguated_gloss.tokens[token_index].tag = "mfs"
				disambiguated_gloss.tokens[token_index].wn_sense_key = most_frequent_sense
				disambiguated_gloss.tokens[token_index].wn_synset_offset = self.reference_wordnet.wordnet["sense_index"][most_frequent_sense]["synset_offset"]
			else:
				print("WHAT")

		return disambiguated_gloss

	def _disambiguate_gloss_by_path_similarity(self, gloss, taggable_tokens, tagged_tokens):

			possible_combinations = map(list, list(self._get_possible_sense_combinations(taggable_tokens, tagged_tokens)))
			total_combs = len(list(possible_combinations))
			scores = []
			pprint(possible_combinations[0])

			print("\ttraversing combs for scores...")
			for i, comb in enumerate(possible_combinations, 1):

				if i % 100 == 0:
					print("\t\t...at comb {0} of {1}".format(i, total_combs))

				# add the gloss synset to the comb to include it in the score
				gloss_data = self.reference_wordnet.wordnet[gloss.pos]["data"][gloss.synset_offset]
				comb.append(("GLOSS_PLACEHOLDER", gloss_data["sense_keys"][0]))
				pairs = list(combinations(comb, 2))
				total_score = 0
				# for each pair calc the score and add them
				for pair in pairs:
					# add score, if no score could be calculated add 0
					total_score += self._calc_path_similarity(pair[0][1], pair[1][1]) or 0

				scores.append(total_score)

			print(scores)

	## Helper Methods ##

	def _get_possible_sense_combinations(self, taggable, tagged):
		"""
		Create a list of possible combinations  of the tokens possible senses.
		"""
		print("\tget possible combinations...")
		# first create a list of the already tagged senses and store for each of those one list inside that contains the one single correct sense
		tagged_sense_keys = [[(token, token.wn_sense_key)] for token in tagged]
		taggable_possible_sense_keys = []

		# for each token that has to be tagged now find all possible senses and collect them
		for token in taggable:
			token_sense_pairs = []
			# for each possible sense of the token add one to the list of that sense
			possible_senses = self._get_possible_wn_senses_for_token(token)
			for single_possible_sense in possible_senses:
				token_sense_pairs.append((token, single_possible_sense))
			taggable_possible_sense_keys.append(token_sense_pairs)

		complete_list_of_tokens = taggable_possible_sense_keys + tagged_sense_keys

		print("\t\t...building combinations")
		# return a dot product of the lists of possible senses of all tokens
		return list_product(*complete_list_of_tokens)

	def _get_possible_wn_senses_for_token(self, token):
		lemmas = token.lemma.split("|")
		possible_wn_senses = []

		for lemma in lemmas:
			lemma_raw, lemma_ss_type = lemma.split("%")
			if int(lemma_ss_type) in GLOSSTAG_POS_POSSIBLE_SS_TYPES[token.pos]:
				lemma_pos = {1: "n", 2: "v", 3: "a", 4: "r", 5: "s"}[int(lemma_ss_type)]
				synsets = wn.synsets(lemma_raw, lemma_pos)

				for synset in synsets:
					for l in synset.lemmas():
						if l.name() == lemma_raw and str(l.key()) in self.reference_wordnet.wordnet["sense_index"]:
							possible_wn_senses.append(l.key())

		return set(possible_wn_senses)

	def _calc_path_similarity(self, sense_key_a, sense_key_b):
		def lemma_from_key(key):
			try:
				return wn.lemma_from_key(key)
			except:
				# there is some strange bug in the glosstag file that somehow does always refer to adjective satellites as adjectives
				# as these keys then cant be found in WN they are tried to be resolved here
				if re.search("%([0-9]):", key).group(1) == "3":
					return lemma_from_key(re.sub("(%)[0-9](:)", "\g<1>5\g<2>", key))
				self._log_key(sense_key_a)
				return None

		lemma_a = lemma_from_key(sense_key_a)
		lemma_b = lemma_from_key(sense_key_b)

		if lemma_a and lemma_b:
			return lemma_a.synset().path_similarity(lemma_b.synset())
		else:
			return 0

	### OTHER METHODS ###

	def _log_key(self, key):
		if key not in self._logged_keys:
			with open(self._invalid_key_logfile, "a") as f:
				f.write(key + "\n")
		self._logged_keys.append(key)

if __name__ == "__main__":
	gd = GlossDisambiguator("", "", "")
	pprint(gd._get_possible_wn_senses_for_token("successive%3"))
