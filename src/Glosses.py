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
		synset_data		(dict)		data entry in wordnet database for the glosses synset
	"""

	def __init__(self, pos, synset_offset, synset_id, gloss_text, synset_data):
		self.__dict__.update(locals())
		del self.__dict__["self"]

		self.tokens = {}

	def __repr__(self):
		return "GLOSS(pos={2}, text={0}, offset={1}".format(self.pos, self.gloss_text, self.synset_offset)

	def gloss_to_transformed_gloss(self, transformed_gloss_string, transformed_gloss_entities):
		return LogicallyTransformedGloss(self.pos, self.synset_offset, self.synset_id, self.gloss_text, self.synset_data, transformed_gloss_string, transformed_gloss_entities)

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

	def __init__(self, pos, synset_offset, synset_id, gloss_text, synset_data, transformed_gloss_string, transformed_gloss_entities):
		super(LogicallyTransformedGloss, self).__init__(pos, synset_offset, synset_id, gloss_text, synset_data)

		self.__dict__.update(locals())
		del self.__dict__["self"]

	def __repr__(self):
		return "TRANSFORMED_GLOSS(pos={2}, text={0}, offset={1}".format(self.pos, self.gloss_text, self.synset_offset)


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

	def __repr__(self):
		return "TOKEN(id={1}, token={0}, sense_key={2}, lemma={3}, pos={4})".format(self.token, self.id, self.wn_sense_key, self.lemma, self.pos)

class CollocationMember(Token):

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
		return "COLLOCATION_MEMBER(id={1}, coll_id={5}, token={0}, sense_key={2}, lemma={3}, coll_lemma={6}, coll_key={7} pos={4})".format(self.token, self.id, self.wn_sense_key, self.lemma, self.pos, self.collocation_id, self.collocation_lemma, self.collocation_wn_sense_key)
