from os import listdir
from os.path import isfile, join
import re
from pprint import pprint

corpus_type = "train"  # train/test/dev
conll_file_source = "data/conll-2012/conll_files/{0}".format(corpus_type)
conll_file_target = "data/conll-2012/"

gold_files = [join(conll_file_source, f) for f in listdir(conll_file_source) if isfile(join(conll_file_source, f)) and re.search(r".+\.v[0-9]_gold_conll", f)]
auto_files = [join(conll_file_source, f) for f in listdir(conll_file_source) if isfile(join(conll_file_source, f)) and re.search(r".+\.v[0-9]_auto_conll", f)]

gold_corpus = ""
auto_corpus = ""

print("GOLD FILES")
for f in gold_files:
	with open(f, "r") as ff:
		gold_corpus += ff.read()

pprint([row for row in gold_corpus.split("\n") if len(row.split()) < 12 and not row == "" and not re.match(r"#.*", row)])


print("AUTO FILES")
for f in auto_files:
	with open(f, "r") as ff:
		auto_corpus += ff.read()

pprint([row for row in auto_corpus.split("\n") if len(row.split()) < 12 and not row == "" and not re.match(r"#.*", row)])

for portion, portion_name, corpus in [(gold_files, "gold", gold_corpus), (auto_files, "auto", auto_corpus)]:
	with open(join(conll_file_target, "full_{0}_corpus_{1}.conll".format(corpus_type, portion_name)), "w") as tf:
		tf.write(corpus)
