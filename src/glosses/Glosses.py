#!/usr/bin/env python
# -*- coding: utf-8 -*-
# AUTHOR: Tonio Weidler

"""Module provides Classes for Glosses and Tokens."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), "../../"))

### GLOSSES ####

class Gloss(object):
	"""Gloss Object representing a gloss of a synset. Somewhat redundant to a Synset Object but its more conveniant to use
	an extra class when it comes to manae subclasses like the LogicallyTransformedGloss.

	Attributes:
		pos						(string)	word class of the glosses synset (noun/adj/adv/verb)
		synset_offset			(string)	synset offset of the glosses synset
		synset_id				(string)	synset id of the glosses synset build from a single letter indicator of the ss_type
											(n/a/v/s/r) followed by the synset_offset
		gloss_text				(string)	the text of the gloss
		gloss_definitions		(list)		definitions of the gloss as list of strings
		gloss_examples			(list)		examples of the gloss as list of strings
		synset					(dict)		the glosses synset object

		tokens					(dict)		dictionary of indexes in the gloss_text and a Token object for the word at that position
											as value

	Methods:
		gloss_to_transformed_gloss		(LogicallyTransformedGloss)		create a Logically Transformed Gloss based on this gloss and
																		the transformed information
	"""

	def __init__(self, pos, synset_offset, synset_id, gloss_text, gloss_definitions, gloss_examples, synset):
		"""Instantiate the Gloss

		Arguments:
			pos						(string)	word class of the glosses synset (noun/adj/adv/verb)
			synset_offset			(string)	synset offset of the glosses synset
			synset_id				(string)	synset id of the glosses synset build from a single letter indicator of the ss_type (n/a/v/s/r) followed by
										the synset_offset
			gloss_text				(string)	the text of the gloss
			gloss_definitions		(list)		definitions of the gloss as list of strings
			gloss_examples			(list)		examples of the gloss as list of strings
			synset					(dict)		the glosses synset object
		"""
		self.__dict__.update(locals())
		del self.__dict__["self"]

		self.tokens = {}

	def __repr__(self):
		"""Informative String Representation of the gloss instance."""
		return "GLOSS(pos={0}, words={3} desc={1}, id={2}".format(self.pos, self.gloss_definitions, self.synset_id, self.synset.words)

	def gloss_to_transformed_gloss(self, transformed_gloss_strings, transformed_gloss_entities, transformed_gloss_parsed):
		"""Create a LogicallyTransformedGloss Object based on this gloss and the transformed information."""
		return LogicallyTransformedGloss(self.pos, self.synset_offset, self.synset_id, self.gloss_text, self.gloss_definitions, self.gloss_examples, self.synset, transformed_gloss_strings, transformed_gloss_entities, transformed_gloss_parsed, self.tokens)

class LogicallyTransformedGloss(Gloss):
	"""Logically transformed gloss (transformation by EasySRL) that contains the same information as the original gloss
	and additionally the trasnformation string, a parsed representation and some preextraced information.

	Attributes:
		pos							(string)	word class of the glosses synset (noun/adj/adv/verb)
		synset_offset				(string)	synset offset of the glosses synset
		synset_id					(string)	synset id of the glosses synset build from a single letter indicator of the ss_type
												(n/a/v/s/r) followed by the synset_offset
		gloss_text					(string)	the text of the gloss
		gloss_definitions			(list)		definitions of the gloss as list of strings
		gloss_examples				(list)		examples of the gloss as list of strings
		synset						(dict)		the glosses synset object

		tokens						(dict)		dictionary of indexes in the gloss_text and a Token object for the word at that position

		transformed_gloss_strings	(list)		list of strings for each gloss definition
		transformed_gloss_entities	(list)		list of dictionaries containing the preextracted info for each gloss transformation
		transformed_gloss_parsed	(list)		list of lists, each inner list is a parsed transformation
	"""

	def __init__(self, pos, synset_offset, synset_id, gloss_text, gloss_definitions, gloss_examples, synset, transformed_gloss_strings, transformed_gloss_entities, transformed_gloss_parsed, tokens):
		"""Instantiate a LogicallyTransformedGloss."""
		super(LogicallyTransformedGloss, self).__init__(pos, synset_offset, synset_id, gloss_text, gloss_definitions, gloss_examples, synset)

		self.__dict__.update(locals())
		del self.__dict__["self"]

	def __repr__(self):
		"""Informative string representation of the LogicallyTransformedGloss."""
		return "TRANSFORMED_GLOSS(pos={0}, words={4} desc={1}, id={2}, transformation={3}".format(self.pos, self.gloss_definitions, self.synset_id, self.transformed_gloss_strings, self.synset.words)


### TOKENS ###

class Token(object):
	"""Token object for words in the glosses.

	Attibutes:
		id						(int):		id of the token inside its gloss, starting with 0
		token					(string):	token in its original form
		lemma 					(string):	the tokens lemma
		wn_synset_offset		(string):	synset offset in DB of the disambiguated token
		wn_sense_key			(string):	sense key in wordnet of the token
		tag						(string):	indicates whether a word was manually, automatically, or not annotated by "wordnet glosstags";
											"ignore" indicates an untaggable word;
											"mfs" indicates it was disambiguated by this system using the most frequent sense baseline
		pos						(string):	POS of that token
		lemma_strings			(set):		a set of different lemmas this token may have in different word classes when not disambiguated
	"""

	def __init__(self, id, token, lemma, wn_synset_offset, wn_sense_key, tag, pos):
		"""Instantiate a Token."""
		self.__dict__.update(locals())
		del self.__dict__["self"]

		self.lemma_strings = set([lemma_string.split("%")[0].lower() for lemma_string in self.lemma.split("|")])

	def __repr__(self):
		"""Informative string representation of the Token Object."""
		return "TOKEN(id={1}, token={0}, sense_key={2}, lemma={3}, pos={4})".format(self.token, self.id, self.wn_sense_key, self.lemma, self.pos)

class CollocationMember(Token):
	"""Special type of Token. Represents a member in a collocation, consisting of multiple words that belong to a single wordnet synset.

	Attributes:
		id						(int):		id of the token inside its gloss, starting with 0
		token					(string):	token in its original form
		lemma 					(string):	the tokens lemma
		wn_synset_offset		(string):	synset offset in DB of the disambiguated token
		wn_sense_key			(string):	sense key in wordnet of the token
		tag						(string):	indicates whether a word was manually, automatically, or not annotated by "wordnet glosstags";
											"ignore" indicates an untaggable word;
											"mfs" indicates it was disambiguated by this system using the most frequent sense baseline
		pos						(string):	POS of that token
		lemma_strings			(set):		a set of different lemmas this token may have in different word classes when not disambiguated

		collocation_id 			(list):		list of ids which are themselves srtings
	"""

	def __init__(self, id, token, lemma, wn_synset_offset, wn_sense_key, tag, pos, collocation_id):
		"""Instantiate the CollocationMember."""
		super(CollocationMember, self).__init__(id, token, lemma, wn_synset_offset, wn_sense_key, tag, pos)

		self.__dict__.update(locals())
		del self.__dict__["self"]

	def __repr__(self):
		"""Informative string representation of the Object."""
		return "COLLOCATION_MEMBER(id={1}, coll_id={5}, token={0}, sense_key={2}, lemma={3}, pos={4})".format(self.token, self.id, self.wn_sense_key, self.lemma, self.pos, self.collocation_id)


class CollocationHead(CollocationMember):
	"""Special type of Token. Represents a head of a collocation, consisting of multiple words that belong to a single wordnet synset.

	Attributes:
		id							(int):		id of the token inside its gloss, starting with 0
		token						(string):	token in its original form
		lemma 						(string):	the tokens lemma
		wn_synset_offset			(string):	synset offset in DB of the disambiguated token
		wn_sense_key				(string):	sense key in wordnet of the token
		tag							(string):	indicates whether a word was manually, automatically, or not annotated by "wordnet glosstags";
												"ignore" indicates an untaggable word;
												"mfs" indicates it was disambiguated by this system using the most frequent sense baseline
		pos							(string):	POS of that token
		lemma_strings				(set):		a set of different lemmas this token may have in different word classes when not disambiguated

		collocation_id 				(list):		list of ids which are themselves strings
		collocation_lemma			(string):	the lemma of the whole collocation, words are seperated by underscores
		collocation_wn_sense_key	(string):	the sense key of the full collocation if disambiguated
		collocation_tag				(string): 	tag indicating if and how the Token/Collocation was disambiguated

	"""

	def __init__(self, id, token, lemma, wn_synset_offset, wn_sense_key, tag, pos, collocation_id, collocation_lemma, collocation_wn_sense_key, collocation_tag):
		"""Instantiate the CollocationHead."""
		super(CollocationHead, self).__init__(id, token, lemma, wn_synset_offset, wn_sense_key, tag, pos, collocation_id)

		self.__dict__.update(locals())
		del self.__dict__["self"]

	def __repr__(self):
		"""Informative string representation of the Object."""
		return "COLLOCATION_HEAD(id={1}, coll_id={5}, token={0}, sense_key={2}, lemma={3}, coll_lemma={6}, coll_key={7} pos={4})".format(self.token, self.id, self.wn_sense_key, self.lemma, self.pos, self.collocation_id, self.collocation_lemma, self.collocation_wn_sense_key)
