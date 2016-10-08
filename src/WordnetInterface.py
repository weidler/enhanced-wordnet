#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), "../"))

import re

from src.functions import get_ss_type_from_sense_key, add_key
from src.glosses.Glosses import Gloss
import src.constants as CONSTANTS

class WordNet(object):
	"""Allows interaction with a WordNet Database. Loads all database files into an representation that allows
	easy interaction with the Synsets and their relations as well as providing methods to extend the relations
	between different Synsets.

	Attributes:
		...

	Public Methods:
		...
	"""


	def __init__(self, wordnet_dir, noun_pointers, adj_pointers, verb_pointers, adv_pointers, relations_filename=None):
		self.__dict__.update(locals())
		del self.__dict__["self"]

		self.wordclasses = ["noun", "adj", "verb", "adv"]
		self.required_files = ["index." + c for c in self.wordclasses] + ["data." + c for c in self.wordclasses] + ["index.sense"]
		self.pointers = {
			"noun": self._load_pointers(noun_pointers),
			"verb": self._load_pointers(verb_pointers),
			"adj": self._load_pointers(adj_pointers),
			"adv": self._load_pointers(adv_pointers)
		}

		self.possible_pointers = list(set([item for sublist in list(self.pointers.values()) for item in sublist]))

		self.lemmas, self.synsets, self.sense_keys = self._load_wordnet(self.wordnet_dir)

		if relations_filename:
			self._integrate_relations_from_file(relations_filename)

	### PUBLIC ###

	def collect_glosses(self):
		"""Collect the glosses of all Synsets and create new gloss objects from them,
		stored in a dictionary using the glosses synset ids as keys."""

		print("collecting glosses...")
		glosses = {}

		for synset_id in self.synsets:
			synset = self.synsets[synset_id]
			if synset_id not in glosses:
				glosses[synset_id] = Gloss(
					pos=synset_id[0],
					synset_offset=synset.offset,
					synset_id=synset_id,
					gloss_text=synset.gloss,
					gloss_definitions=synset.definitions,
					gloss_examples=synset.examples,
					synset=synset
				)
			else:
				print("recognized synset offset duplicate")

		print("\t... finished")
		return glosses

	def synset_from_id(self, synset_id):
		"""From a synset id get the according synset."""
		return self.synsets[synset_id]

	def synset_from_key(self, sense_key):
		"""From a sense key get the according synset."""
		ss_type = get_ss_type_from_sense_key(sense_key)
		return self.synsets[ss_type + self.sense_keys[sense_key]["synset_offset"]]

	def synset_id_from_key(self, sense_key):
		"""From a sense key get the according synset."""
		ss_type = get_ss_type_from_sense_key(sense_key)
		if sense_key not in self.sense_keys.keys() and ss_type == "a":
			sense_key = re.sub(r"(%)3(:)", "\g<1>5\g<2>", sense_key)
		if sense_key not in self.sense_keys:
			raise AttributeError("Key {0} doesnt exist!".format(sense_key))

		return ss_type + self.sense_keys[sense_key]["synset_offset"]

	def synsets_for_lemma(self, lemma, wordclass):
		"""Return a list of Synset Objects that can represent this lemma."""
		synsets = []
		if lemma in self.lemmas[wordclass]:
			for offset in self.lemmas[wordclass][lemma]["synset_offsets"]:
				synset_id = CONSTANTS.WORDCLASS_SS_TYPE_MAPPING[wordclass]+offset
				if synset_id in self.synsets:
					synsets.append(self.synsets[synset_id])
				elif synset_id[0] == "a" and "s"+offset in self.synsets:
					synsets.append(self.synsets["s"+offset])

		return synsets

	def get_hypernym_synsets(self, snyset):
		"""For a given Synset return a list of Synsets that are its hypernyms."""
		if "hypernyms":
			hypernym_ids = synset.relations.hyper

	### PROTECTED ###

	def _load_wordnet(self, wordnet_dir):
		print("=== Loading WordNet... ===")
		# get files in dir
		files = [os.path.join(wordnet_dir, f) for f in os.listdir(wordnet_dir)]
		missing_files = []

		# check if all files needed exist
		for f in self.required_files:
			if os.path.join(wordnet_dir, f) not in files:
				missing_files.append(f)

		if len(missing_files) != 0:
			raise Exception("Loading Failed! Missing file(s) in provided WordNet Directory: {0}".format(", ".join(missing_files)))

		# load files
		lemmas = {}
		synsets = {}

		# parse sense index file
		with open(os.path.join(wordnet_dir, "index.sense")) as f:
			sense_keys = self._parse_sense_index_file(f.read())

		# for all wordclasses pass the database files
		for wordclass in self.wordclasses:
			print("parsing {0} files...".format(wordclass))

			# parse index file
			lemmas[wordclass] = {}
			with open(os.path.join(wordnet_dir, "index." + wordclass)) as f:
				print("\t...index")
				lemmas[wordclass] = self._parse_index_file(f.read())

			# parse data file
			with open(os.path.join(wordnet_dir, "data." + wordclass)) as f:
				print("\t...data")
				parsed_data_file = self._join_data_with_sense_keys(self._parse_data_file(f.read(), self.pointers[wordclass]), sense_keys, wordclass)

				print("...creating synsets")
				# create the synsets
				for offset in parsed_data_file:
					offset_data = parsed_data_file[offset]
					synset_id = offset_data["ss_type"] + offset
					relations = self._relations_from_pointers(offset_data["pointers"], wordclass)
					synsets[synset_id] = Synset(synset_id=synset_id, sense_keys=offset_data["sense_keys"], relations=relations, gloss=offset_data["gloss"], words=offset_data["words"])

		print("...finished")
		return lemmas, synsets, sense_keys

	def _parse_index_file(self, file_content):
		"""
		Parse the content of an index.POS file to a dictionary representation that stores the lemmas as keys and the according information as an additional dict.

		Key Arguments:
			file_content	(string):	the content of an index file.

		Returns:
			dict:	dict with lemmas as keys, name-value mappings as values
		"""
		lines = [line.strip().split(" ") for line in file_content.split("\n") if line[:2] != "  " and len(line.strip().split(" ")) > 1]
		index = {}

		for word in lines:
			if word[0] not in index:
				index[word[0]] = {  # word[0] -> lemma
					"pos": word[1],
					"synset_cnt": word[2],
					"p_cnt": word[3],
					"ptr_symbol": word[4:4+int(word[3])],
					"sense_cnt": word[4+int(word[3])],
					"tagsense_cnt": word[4+int(word[3])+1],
					"synset_offsets": word[4+int(word[3])+2:]
				}
			else:
				print("Omitting duplicate index entry!")

		return index

	def _parse_data_file(self, file_content, pointers):
		"""
		Parse the content of a data.POS file to a dictionary representation with synset offsets as keys and the rest of the information as their values.

		Key Arguments:
			file_content	(string):	the content of a data file
			pointers		(dict):		pointers and their description that are used in this data file

		Returns:
			dict:	synset offsets as keys, info as values
		"""
		lines = [line.strip().split(" ") for line in file_content.split("\n") if line[:2] != "  " and len(line.strip().split(" ")) > 1]
		data = {}

		for word in lines:
			if word[0] not in data:
				word_chunk_length = 2
				word_info = {
					"lex_filenum": word[1],
					"ss_type": word[2],
					"w_cnt": int(word[3], 16),
					"p_cnt": int(word[4+int(word[3], 16)*2]),
					"gloss": " ".join(word[word.index("|")+1:]),
					"sense_keys": []  # will be filled by another function
				}

				word_list = [(w, word[4:4+word_info["w_cnt"]*word_chunk_length+1][i+1]) for i, w in list(enumerate(word[4:4+word_info["w_cnt"]*word_chunk_length]))[::2]]
				pointers = [word[4+word_info["w_cnt"]*word_chunk_length+1:4+word_info["w_cnt"]*word_chunk_length+1 + word_info["p_cnt"]*4][i:i+4] for i in range(0, word_info["p_cnt"]*4, 4)]

				word_info.update({
					"words": word_list,
					"pointers": pointers
				})

				if word_info["ss_type"] == "v":
					f_cnt_position = int(4 + (word_info["w_cnt"] * word_chunk_length) + 1 + (word_info["p_cnt"] * 4))
					f_cnt = int(word[f_cnt_position], 16)
					frame_list = [word[f_cnt_position+1:f_cnt_position+1+f_cnt*3][i+1:i+3] for i in range(0, f_cnt*3, 3)]

					word_info.update({
						"f_cnt": f_cnt,
						"frames": frame_list
					})

				data[word[0]] = word_info

			else:
				print("Omitting duplicate data entry!")

		return data

	def _parse_sense_index_file(self, file_content):
		lines = [line.strip().split(" ") for line in file_content.split("\n") if line[:2] != "  " and len(line.strip().split(" ")) > 1]
		index = {}

		for word in lines:
			if word[0] not in index:
				index[word[0]] = {
					"synset_offset": word[1],
					"sense_number": word[2],
					"tag_cnt": word[3]
				}
			else:
				print("DUPLICATE SENSE INDEX!")

		return index

	def _join_data_with_sense_keys(self, data, sense_index, pos):
		print("\t...sense keys")
		joined = data
		pos = {"noun": ["1"], "verb": ["2"], "adj": ["3", "5"], "adv": ["4"]}[pos]

		mso = 0

		for sense_key in sense_index:
			sense_key_info = sense_index[sense_key]
			synset_offset = sense_key_info["synset_offset"]
			if synset_offset in data:
				joined[synset_offset]["sense_keys"].append(sense_key)
			elif synset_offset not in data and re.search("%([0-9]+):", sense_key).group(1) in pos:
				print(synset_offset)
				mso += 1

		print("\t\t{0} missing synsets".format(mso))
		return joined

	def _load_pointers(self, pointer_file):
		with open(pointer_file) as f:
			return {pointer.strip(): description for (pointer, description) in [re.split(" {4,}|\t", line) for line in f.read().split("\n") if len(line.split("    ")) == 2]}

	def _relations_from_pointers(self, pointers, wordclass):
		"""From a Data File List of Pointers of a synset retrieve the relations and return them as a dictionary."""

		relations = {}
		for pointer in pointers:
			relation_name = self.pointers[wordclass][pointer[0]]
			if relation_name not in relations.keys():
				relations[relation_name] = []
			relations[relation_name].append(pointer[2] + pointer[1])

		return relations

	def _integrate_relations_from_file(self, filename):
		print("...integrating new relations")
		import pickle
		# TODO implement inverse relations

		with open(filename, "rb") as f:
			relations = pickle.load(f)
		for synset_id in relations:
			self.synsets[synset_id].update_relations(relations[synset_id], self)


class Synset(object):
	"""
		Attributes:
		synset_id		(string)		combination of the ss_type and the offset of the synset to uniquely
										identify the synset e.g. 'n03428529'
		ss_type			(string)		single character indicating the pos of the synset -> n/v/a/s/r
		offset			(string)		8 digit byte offset of the synset in the original wordnet database file of its ss_type
		sense_keys		(list)			the sense keys that are contained in the synset uniquely identifying a sense of a lemma,
										in the following format: lemmy%ss_type:lex_filenum:lex_id:head_word:head_id
										e.g. 'disease%1:26:00::'
		words			(list)			words as annotated by lexicographer, case sensitive
		relations		(dict)			keys are the relation names while values are synset_ids to the synsets the relation holds with
										these values may also be tuples for ternary relations
		gloss			(string)		the full gloss
		definitions		(list)			a list of definitions as found in the gloss
		examples		(list)			a list of examples as found in the gloss
	"""

	def __eq__(self, other):
		return self.synset_id == other.synset_id

	def __repr__(self):
		return "Synset({0}, {1})".format(self.synset_id, self.words)

	def __init__(self, synset_id, sense_keys, words, relations, gloss):
		self.__dict__.update(locals())
		del self.__dict__["self"]

		self.ss_type = synset_id[0]
		self.offset = synset_id[1:]

		gloss_parts = [part.strip() for part in gloss.split(";")]
		self.definitions = [part for part in gloss_parts if not part.startswith('"') or not part.endswith('"')]
		self.examples = [part for part in gloss_parts if part.startswith('"') and part.endswith('"')]

	def update_relations(self, relations, wordnet):
		for relation_type in relations:
			add_key(relation_type, self.relations, value=[])
			for rel_member in relations[relation_type]:
				if isinstance(rel_member, tuple) or isinstance(rel_member, list):
					self.relations[relation_type].append(tuple(map(lambda m: wordnet.synset_id_from_key(m), rel_member)))
				else:
					self.relations[relation_type].append(wordnet.synset_id_from_key(rel_member))

if __name__ == "__main__":
	wn = WordNet("data/wordnet_database/", "src/pointers/noun_pointers.txt", "src/pointers/adj_pointers.txt", "src/pointers/verb_pointers.txt", "src/pointers/adv_pointers.txt", relations_filename="extracted_data/relations_dev_117659.rel")
	whips = wn.synsets_for_lemma("whip", "noun")
	for w in whips:
		if "attributes" in w.relations:
			print(w.gloss)
			print(w.relations["attributes"])
	# sys.exit()
	syn = wn.synsets["n02084071"]
	syn2 = wn.synsets["n00001930"]
	syn3 = wn.synsets["n02084071"]
	syn3.relations = {}

	print(syn == syn2)
	print(syn == syn3)
	sys.exit()

	print(syn.ss_type)
	print(syn.offset)
	print(syn.sense_keys)
	print(syn.relations)
	print(syn.definitions)
	print(syn.examples)

	for k in syn.sense_keys:
		print(wn.synset_from_key(k))
