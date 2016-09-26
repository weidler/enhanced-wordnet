#!/usr/bin/env python
# -*- coding: utf-8 -*-
# AUTHOR: Tonio Weidler

import subprocess as sp
import re
import os
import json
import datetime

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
		print("EMPTY GLOSSES:\n{0}".format([g for g in self._gloss_order if self.glosses[g].gloss_text == ""]))
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
		transformed_glosses_list = [g for g in content.split("\n")]

		transformed_glosses = re.sub("%.*\n", "", content)
		# transformed_glosses_list = [g for g in transformed_glosses.split("\n")]
		print("{0} vs. {1}".format(len(transformed_glosses_list), len(self._gloss_order)))

		return self._extend_glosses_with_transformations(transformed_glosses_list)

	def _extend_glosses_with_transformations(self, transformed_gloss_strings):
		transformed_glosses = {}
		for i, gloss_key in enumerate(self._gloss_order):
			gloss = self.glosses[gloss_key]
			gloss_transformation_string = transformed_gloss_strings[i]

			transformed_glosses[gloss_key] = gloss.gloss_to_transformed_gloss(gloss_transformation_string, self._parse_transformation(gloss_transformation_string))

		return transformed_glosses


	def _parse_transformation(self, transformed_gloss):
		return("penis")

	def _apply_parsing_tool(self, gloss_corpus):
		with open("gloss_corpus.tmp", "w") as f:
			f.write(gloss_corpus)

		try:
			parser_output = sp.check_output("java -Xmx2g -jar src/tools/easysrl/easysrl.jar --model src/tools/easysrl/model/ --maxLength 150 --outputFormat {0} --inputFile gloss_corpus.tmp 2>{1}".format(self._transformation_type, "PARSER_LOG_"+self._logfile), shell=True)
		except sp.CalledProcessError as e:
			return e.output

		os.remove("gloss_corpus.tmp")

		return parser_output

	def _build_gloss_corpus(self, glosses):
		gloss_corpus = ""

		for gloss_key in self._gloss_order:
			gloss = self.glosses[gloss_key]
			if gloss.gloss_text != "":
				gloss_corpus += gloss.gloss_text + "\n"
			else:
				gloss_corpus += "PLACEHOLDER" + "\n"
				self._log_error("WARNING: Empty Gloss", gloss)

		print("GLOSS CORPUS LENGTH: {0}".format(len(gloss_corpus.split("\n"))))
		return gloss_corpus

	def _log_error(self, message, gloss):
		with open(self._logfile, "a") as f:
			f.write("{0}\n\t\t{1}\n".format(message, gloss))
