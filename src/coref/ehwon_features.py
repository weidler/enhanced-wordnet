"""Additional Cort Features based on Enhanced WordNet."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), "../../"))

from cort.core.mentions import Mention
from cort.core.documents import Document

from pprint import pprint
import random as ran
from nltk.stem import WordNetLemmatizer
import itertools

from src.WordnetInterface import WordNet
import src.constants as CONSTANTS
from src.functions import is_noun, is_verb

# there is the need to create an global wordnet interface here, that can be used in the functions
# else, with every function call it would have to be reinitialized

GLOBAL_WORDNET_INTERFACE = WordNet("data/wordnet_database/", "src/pointers/noun_pointers.txt", "src/pointers/adj_pointers.txt", "src/pointers/verb_pointers.txt", "src/pointers/adv_pointers.txt", relations_filename="extracted_data/relations_dev_117659.rel")
wnl = WordNetLemmatizer()

def random_feature(mention):
    """Random test."""
    return "fine_type", ran.randint(0, 10)

def antecedent_attribute_congruency(anaphor, antecedent):
    """Compute the congruency between the antecedents EhWoN attributes and the anaphors adjectival modifiers."""
    match_score = _calc_mention_attribute_congruency(phrase=anaphor, paraphrase=antecedent)
    return ("antecedent_attribute_congruency", match_score)

def anaphor_attribute_congruency(anaphor, antecedent):
    """Compute the congruency between the anaphors EhWoN attributes and the antecedents adjectival modifiers."""
    match_score = _calc_mention_attribute_congruency(phrase=antecedent, paraphrase=anaphor)
    return ("anaphor_attribute_congruency", match_score)

def antecedent_specifier_congruency(anaphor, antecedent):
    """???."""
    pass

def anaphor_specifier_congruency(anaphor, antecedent):
    """???."""
    pass

def anaphor_performs_antecedent_functionality(anaphor, antecedent):
    """Compute whether the anaphor is subject of a verb that is the antecedents functionality."""

def antecedent_performs_anaphor_functionality(anaphor, antecedent):
    """Compute whether the antecedent is subject of a verb that is the anaphors functionality."""

def anaphor_performs_antecedent_application(anaphor, antecedent):
    """Compute whether the anaphor is object of a verb that is the antecedents application."""
    performs = _calc_typical_action_congruency(anaphor, antecedent)
    return ("anaphor_performs_antecedent_application", performs)

def antecedent_performs_anaphor_application(anaphor, antecedent):
    """Compute whether the antecedent is object of a verb that is the anaphors application."""
    performs = _calc_typical_action_congruency(anaphor, antecedent)
    return ("antecedent_performs_anaphor_application", performs)

### HELPER FUNCTIONS ###

def _calc_typical_action_congruency(phrase, paraphrase):
    # TODO include subj/obj restriction
    """Calculate if the phrase performs an action which is typical for the paraphrase."""
    phrase_performs_paraphrase_action = False

    phrase_dependency_structure = list(itertools.chain(*phrase.document.dep))[phrase.span.begin:phrase.span.end+1]
    sentence_dependency_structure = phrase.document.dep[phrase.attributes["sentence_id"]]
    phrase_head_dependency_token = phrase_dependency_structure[phrase.attributes["head_index"]]
    phrase_head_governor_token = sentence_dependency_structure[phrase_head_dependency_token.head-1]
    phrase_head_governor_synset_ids = set([syn.synset_id for syn in GLOBAL_WORDNET_INTERFACE.synsets_for_lemma(wnl.lemmatize(phrase_head_governor_token.form), "verb")])

    paraphrase_dependency_structure = list(itertools.chain(*paraphrase.document.dep))[paraphrase.span.begin:paraphrase.span.end+1]
    paraphrase_head_dependency_token = paraphrase_dependency_structure[paraphrase.attributes["head_index"]]
    paraphrase_head_lemma = wnl.lemmatize(paraphrase_head_dependency_token.form, "n").lower()
    paraphrase_head_synsets = GLOBAL_WORDNET_INTERFACE.synsets_for_lemma(paraphrase_head_lemma, "noun")

    if paraphrase_head_synsets and is_verb(phrase_head_governor_token.pos) and phrase_head_governor_synset_ids:
        paraphrase_head_application_synset_ids = set(itertools.chain(*[syn.relations["application"] for syn in paraphrase_head_synsets if "application" in syn.relations]))
        if not phrase_head_governor_synset_ids.isdisjoint(paraphrase_head_application_synset_ids):
            phrase_performs_paraphrase_action = True
            print("\n'{0}' performing '{1}' which is typical for a '{2}'".format(phrase_head_dependency_token.form ,phrase_head_governor_token.form, paraphrase_head_lemma))

    return phrase_performs_paraphrase_action

def _calc_mention_attribute_congruency(phrase, paraphrase):
    """Calculate the attributal congruency between a mention's (phrase) adjectives and another mention's (paraphrase) wordnet attributes."""

    phrase_dependency_structure = list(itertools.chain(*phrase.document.dep))[phrase.span.begin:phrase.span.end+1]
    phrase_head_dependency_token = phrase_dependency_structure[phrase.attributes["head_index"]]
    phrase_head_adjectives = [t for t in phrase.document.dep[phrase.attributes["sentence_id"]] if t.head == phrase_head_dependency_token.index and t.pos in CONSTANTS.ADJECTIVE_POS]
    phrase_head_adjective_lemmas = [wnl.lemmatize(t.form, "a").lower() for t in phrase_head_adjectives]
    phrase_head_adjectives_synset_ids = list(itertools.chain(*[[syn.synset_id for syn in GLOBAL_WORDNET_INTERFACE.synsets_for_lemma(adjective, "adj")] for adjective in phrase_head_adjective_lemmas]))

    paraphrase_dependency_structure = list(itertools.chain(*paraphrase.document.dep))[paraphrase.span.begin:paraphrase.span.end+1]
    paraphrase_head_dependency_token = paraphrase_dependency_structure[paraphrase.attributes["head_index"]]
    paraphrase_head_lemma = wnl.lemmatize(paraphrase_head_dependency_token.form, "n").lower()

    match_score = 0
    if phrase_head_adjectives and paraphrase_head_dependency_token.pos in CONSTANTS.NOUN_POS:
        possible_synsets = GLOBAL_WORDNET_INTERFACE.synsets_for_lemma(paraphrase_head_lemma, "noun")
        if not possible_synsets: return match_score
        poss_matches = [0 for poss in range(len(possible_synsets))]
        poss_max_matches = [0 for poss in range(len(possible_synsets))]

        # as there are not enough annotated senses simply the synset with the most matches will be used
        for i, syn in enumerate(possible_synsets):
            if "attributes" not in syn.relations.keys(): continue
            poss_max_matches[i] = len(syn.relations["attributes"])
            for attr in syn.relations["attributes"]:
                if attr in phrase_head_adjectives_synset_ids:
                    poss_matches[i] += 1

        attribute_matches = max(poss_matches)
        max_attribute_matches_possible = poss_max_matches[poss_matches.index(attribute_matches)]

        # TODO score needs to be improved
        match_score = attribute_matches

    return match_score
