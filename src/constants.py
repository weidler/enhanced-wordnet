"""Module containing different constants that may be reused over the whole source code."""

SS_TYPE_LIST = ["n", "v", "r", "a", "s"]
WORDCLASS_SS_TYPE_MAPPING = {
	"noun": "n",
	"verb": "v",
	"adj": "a",
	"adv": "r",
}
SS_TYPE_WORDCLASS_MAPPING = {
	"n": "noun",
	"v": "verb",
	"a": "adj",
	"r": "adv",
	"s": "adj"
}

ADJECTIVE_POS = ["JJ", "JJS", "JJR"]
NOUN_POS = ["NN", "NNS", "NNP", "NNPS"]
ADVERB_POS = ["RB", "RBR", "RBS"]
VERB_POS = ["VB", "VBD", "VBG", "VBN", "VBP", "VBZ"]
