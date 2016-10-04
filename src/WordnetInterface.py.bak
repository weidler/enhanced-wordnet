#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
from pprint import pprint

from src.Glosses import Gloss, LogicallyTransformedGloss

class WordNet(object):

	def __init__(self, wordnet_dir, noun_pointers, adj_pointers, verb_pointers, adv_pointers):
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

		self.possible_pointers = list(set([item for sublist in self.pointers.values() for item in sublist]))

		self.wordnet = self._load_wordnet(self.wordnet_dir)

	def collect_glosses(self, recognize_pos=["noun", "verb", "adj", "adv"]):
		print("collecting glosses...")
		glosses = {}
		for pos in recognize_pos:
			# TODO was ist mit den satelites?
			id_prefix = {"noun": "n", "verb": "v", "adj": "a", "adv": "r"}[pos]
			for synset in self.wordnet[pos]["data"]:
				if id_prefix+synset not in glosses:
					glosses[id_prefix+synset] = Gloss(pos, synset, id_prefix+synset, self.wordnet[pos]["data"][synset]["gloss"], self.wordnet[pos]["data"][synset])
				else:
					print("recognized synset offset duplicate")
		print("\t... finished")
		return glosses


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
		pos_data = {}
		with open(os.path.join(wordnet_dir, "index.sense")) as f:
			sense_indexes = self._parse_sense_index_file(f.read())
		for pos in self.wordclasses:
			print("parsing {0} files...".format(pos))
			pos_data[pos] = {}
			with open(os.path.join(wordnet_dir, "index." + pos)) as f:
				print("\t...index")
				pos_data[pos]["index"] = self._parse_index_file(f.read())

			with open(os.path.join(wordnet_dir, "data." + pos)) as f:
				print("\t...data")
				pos_data[pos]["data"] = self._join_data_with_sense_keys(self._parse_data_file(f.read(), self.pointers[pos]), sense_indexes, pos)

		pos_data["sense_index"] = sense_indexes

		print("loaded wordnet database...")
		return pos_data

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
				index[word[0]] = {
					"pos": word[1],
					"synset_cnt": word[2],
					"p_cnt": word[3],
					"ptr_symbol": word[4:4+int(word[3])],
					"sense_cnt": word[4+int(word[3])],
					"tagsense_cnt": word[4+int(word[3])+1],
					"synset_offset": word[4+int(word[3])+2:]
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

			# pprint(data[word[0]])
		return data

	def _load_pointers(self, pointer_file):
		with open(pointer_file) as f:
			return {pointer.strip(): description for (pointer, description) in [re.split(" {4,}|\t", line) for line in f.read().split("\n") if len(line.split("    ")) == 2]}

if __name__ == "__main__":
	wn = WordNet("data/wordnet_database/", "src/noun_pointers.txt", "src/adj_pointers.txt", "src/verb_pointers.txt", "src/adv_pointers.txt")

	p = 0
	for i in wn.wordnet["noun"]["data"]:
		if p < 10:
			pprint(wn.wordnet["noun"]["data"][i])
		else:
			break
		p += 1
