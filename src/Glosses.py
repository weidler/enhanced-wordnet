#!/usr/bin/env python
# -*- coding: utf-8 -*-

### GLOSSES ####

class Gloss(object):
	"""
	Attributes:
		pos				(string)	word class of the glosses synset (noun/adj/adv/verb)
		synset_offset	(string)	synset offset of the glosses synset
		synset_id		(string)	synset id of the glosses synset build from a single letter indicator of the ss_type (n/a/v/s/r) followed by
									the synset_offset
		gloss_text		(string)	the text of the gloss
		gloss_desc		(string)	description part of the gloss
		synset_data		(dict)		data entry in wordnet database for the glosses synset
	"""

	def __init__(self, pos, synset_offset, synset_id, gloss_text, synset_data):
		self.__dict__.update(locals())
		del self.__dict__["self"]

		self.tokens = {}
		gloss_parts = gloss_text.split("; ")
		self.gloss_desc = "; ".join([p for p in gloss_parts if p[0] != '"'])

	def __repr__(self):
		return "GLOSS(pos={0}, words={3} desc={1}, id={2}".format(self.pos, self.gloss_desc, self.synset_id, self.synset_data["words"])

	def gloss_to_transformed_gloss(self, transformed_gloss_string, transformed_gloss_entities):
		return LogicallyTransformedGloss(self.pos, self.synset_offset, self.synset_id, self.gloss_text, self.synset_data, transformed_gloss_string, transformed_gloss_entities, self.tokens)

class LogicallyTransformedGloss(Gloss):
	"""
	Attributes:
		pos							(string)	word class of the glosses synset (noun/adj/adv/verb)
		synset_offset				(string)	synset offset of the glosses synset
		synset_id					(string)	synset id of the glosses synset build from a single letter indicator of the ss_type (n/a/v/s/r) followed by
									the synset_offset
		gloss_text					(string)	the text of the gloss
		synset_data					(dict)		data entry in wordnet database for the glosses synset

		transformed_gloss_string	(string)	string representation of the transformed gloss
		transformed_gloss_entities	(dict)		entities of the gloss and their respective predicates
	"""

	def __init__(self, pos, synset_offset, synset_id, gloss_text, synset_data, transformed_gloss_string, transformed_gloss_entities, tokens):
		super(LogicallyTransformedGloss, self).__init__(pos, synset_offset, synset_id, gloss_text, synset_data)

		self.__dict__.update(locals())
		del self.__dict__["self"]

	def __repr__(self):
		return "TRANSFORMED_GLOSS(pos={0}, words={4} desc={1}, id={2}, transformation={3}".format(self.pos, self.gloss_desc, self.synset_id, self.transformed_gloss_string, self.synset_data["words"])


### TOKENS ###

class Token(object):
	"""
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
	"""

	def __init__(self, id, token, lemma, wn_synset_offset, wn_sense_key, tag, pos):
		self.__dict__.update(locals())
		del self.__dict__["self"]

		self.lemma_string = self.lemma.split("|")[0].split("%")[0].lower()

	def __repr__(self):
		return "TOKEN(id={1}, token={0}, sense_key={2}, lemma={3}, pos={4})".format(self.token, self.id, self.wn_sense_key, self.lemma, self.pos)

class CollocationMember(Token):
	"""
	Attributes:
		collocation_id 			(list):		list of ids which are themselves srtings
	"""

	def __init__(self, id, token, lemma, wn_synset_offset, wn_sense_key, tag, pos, collocation_id):
		super(CollocationMember, self).__init__(id, token, lemma, wn_synset_offset, wn_sense_key, tag, pos)

		self.__dict__.update(locals())
		del self.__dict__["self"]

	def __repr__(self):
		return "COLLOCATION_MEMBER(id={1}, coll_id={5}, token={0}, sense_key={2}, lemma={3}, pos={4})".format(self.token, self.id, self.wn_sense_key, self.lemma, self.pos, self.collocation_id)


class CollocationHead(CollocationMember):

	def __init__(self, id, token, lemma, wn_synset_offset, wn_sense_key, tag, pos, collocation_id, collocation_lemma, collocation_wn_sense_key, collocation_tag):
		super(CollocationHead, self).__init__(id, token, lemma, wn_synset_offset, wn_sense_key, tag, pos, collocation_id)

		self.__dict__.update(locals())
		del self.__dict__["self"]

	def __repr__(self):
		return "COLLOCATION_HEAD(id={1}, coll_id={5}, token={0}, sense_key={2}, lemma={3}, coll_lemma={6}, coll_key={7} pos={4})".format(self.token, self.id, self.wn_sense_key, self.lemma, self.pos, self.collocation_id, self.collocation_lemma, self.collocation_wn_sense_key)
