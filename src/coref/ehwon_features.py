#!/usr/bin/env python
# -*- coding: utf-8 -*-
# AUTHOR: Tonio Weidler

"""Additional Cort Features based on Enhanced WordNet."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), "../../"))

from pprint import pprint
from nltk.stem import WordNetLemmatizer
import itertools

from src.WordnetInterface import WordNet
import src.constants as CONSTANTS
from src.util import is_verb, is_subj, is_obj

# there is the need to create an global wordnet interface here, that can be used in the functions
# else, with every function call it would have to be reinitialized

GLOBAL_WORDNET_INTERFACE = WordNet("data/wordnet_database/", "src/pointers/noun_pointers.txt", "src/pointers/adj_pointers.txt", "src/pointers/verb_pointers.txt", "src/pointers/adv_pointers.txt", relations_filename="extracted_data/relations_final_full.rel")
wnl = WordNetLemmatizer()

def antecedent_attribute_specification(anaphor, antecedent):
    """Compute whether the anaphor is a hypernym of the antecedent, specified by adjectives that are attributes of the antecedent.

    Returns:
        (tuple):    feature name, boolean
    """
    matches = _calc_attribute_specification(phrase=anaphor, paraphrase=antecedent)
    return "antecedent_attribute_specification", matches

def anaphor_attribute_specification(anaphor, antecedent):
    """Compute whether the antecedent is a hypernym of the anaphor, specified by adjectives that are attributes of the anaphor.

    Returns:
        (tuple):    feature name, boolean
    """
    matches = _calc_attribute_specification(phrase=antecedent, paraphrase=anaphor)
    return "anaphor_attribute_specification", matches

def anaphor_performs_antecedent_function(anaphor, antecedent):
    """Compute whether the anaphor is object of a verb that is the antecedents function.

    Returns:
        (tuple):    feature name, boolean
    """
    performs = _calc_typical_action_congruency(anaphor, antecedent)
    return "anaphor_performs_antecedent_function", performs

def antecedent_performs_anaphor_function(anaphor, antecedent):
    """Compute whether the antecedent is object of a verb that is the anaphors function.

    Returns:
        (tuple):    feature name, boolean
    """
    performs = _calc_typical_action_congruency(antecedent, anaphor)
    return "antecedent_performs_anaphor_function", performs

### HELPER FUNCTIONS ###

def _calc_typical_action_congruency(phrase, paraphrase):
    """Calculate if the phrase performs an action which is typical for the paraphrase.

    Returns:
        (bool): true if the head of the paraphrase performs an action that is the function of the phrase head
    """
    phrase_performs_paraphrase_action = False

    phrase_dependency_structure = list(itertools.chain(*phrase.document.dep))[phrase.span.begin:phrase.span.end+1]
    sentence_dependency_structure = phrase.document.dep[phrase.attributes["sentence_id"]]
    phrase_head_dependency_token = phrase_dependency_structure[phrase.attributes["head_index"]]
    phrase_head_governor_token = sentence_dependency_structure[phrase_head_dependency_token.head-1]

    if not is_verb(phrase_head_governor_token.pos): return phrase_performs_paraphrase_action
    if not is_subj(phrase_head_dependency_token.deprel) and not is_obj(phrase_head_dependency_token.deprel): return phrase_performs_paraphrase_action

    phrase_head_governor_synsets = set([syn for syn in GLOBAL_WORDNET_INTERFACE.synsets_for_lemma(wnl.lemmatize(phrase_head_governor_token.form), "verb")])

    if not phrase_head_governor_synsets: return phrase_performs_paraphrase_action

    potential_typical_actions = set(list(itertools.chain(*[GLOBAL_WORDNET_INTERFACE.get_hypernym_synsets(syn, traversal_depth=0) for syn in phrase_head_governor_synsets])) + list(phrase_head_governor_synsets))
    potential_typical_actions_synset_ids = set([syn.synset_id for syn in potential_typical_actions])

    paraphrase_dependency_structure = list(itertools.chain(*paraphrase.document.dep))[paraphrase.span.begin:paraphrase.span.end+1]
    paraphrase_head_dependency_token = paraphrase_dependency_structure[paraphrase.attributes["head_index"]]
    paraphrase_head_lemma = wnl.lemmatize(paraphrase_head_dependency_token.form, "n").lower()
    paraphrase_head_synsets = GLOBAL_WORDNET_INTERFACE.synsets_for_lemma(paraphrase_head_lemma, "noun")

    if paraphrase_head_synsets and is_verb(phrase_head_governor_token.pos) and potential_typical_actions_synset_ids:
        paraphrase_head_function_synset_ids = set(itertools.chain(*[syn.relations["function"] for syn in paraphrase_head_synsets if "function" in syn.relations]))
        if not potential_typical_actions_synset_ids.isdisjoint(paraphrase_head_function_synset_ids):
            phrase_performs_paraphrase_action = True
            # print("'{0}' performing '{1}' which is typical for a '{2}'".format(phrase_head_dependency_token.form, phrase_head_governor_token.form, paraphrase_head_lemma))

    return phrase_performs_paraphrase_action

def _calc_attribute_specification(phrase, paraphrase):
    """Calculate if a mention (paraphrase) is a hypernym of another mention (phrase) and is modified by adjectives that are the phrases attributes.

    Returns:
        (bool):     True if there is a match in hypernymy and attribute/adjectives
    """
    # add CONTRADICTION -> an emerald CANT BE RED
    # get necessary informations about the paraphrase
    specifies_with_attributes = False
    paraphrase_dependency_structure = list(itertools.chain(*paraphrase.document.dep))[paraphrase.span.begin:paraphrase.span.end+1]
    paraphrase_head_dependency_token = paraphrase_dependency_structure[paraphrase.attributes["head_index"]]
    paraphrase_head_lemma = wnl.lemmatize(paraphrase_head_dependency_token.form, "n").lower()
    paraphrase_head_synsets = set(GLOBAL_WORDNET_INTERFACE.synsets_for_lemma(paraphrase_head_lemma, "noun"))

    paraphrase_head_adjectives = [t for t in paraphrase.document.dep[paraphrase.attributes["sentence_id"]] if t.head == paraphrase_head_dependency_token.index and t.pos in CONSTANTS.ADJECTIVE_POS]

    # if the paraphrase has no adjectives at all simply return False as there cant be any congruency then
    if not paraphrase_head_adjectives: return specifies_with_attributes

    paraphrase_head_adjective_lemmas = [wnl.lemmatize(t.form, "a").lower() for t in paraphrase_head_adjectives]
    paraphrase_head_adjectives_synsets = list(itertools.chain(*[[syn for syn in GLOBAL_WORDNET_INTERFACE.synsets_for_lemma(adjective, "adj")] for adjective in paraphrase_head_adjective_lemmas]))
    paraphrase_head_adjectives_synset_ids = set([syn.synset_id for syn in paraphrase_head_adjectives_synsets])

    # get necessary informations about the phrase
    phrase_dependency_structure = list(itertools.chain(*phrase.document.dep))[phrase.span.begin:phrase.span.end+1]
    phrase_head_dependency_token = phrase_dependency_structure[phrase.attributes["head_index"]]

    if phrase_head_dependency_token.pos not in CONSTANTS.NOUN_POS: return specifies_with_attributes

    phrase_head_lemma = wnl.lemmatize(phrase_head_dependency_token.form, "n").lower()
    phrase_head_synsets = GLOBAL_WORDNET_INTERFACE.synsets_for_lemma(phrase_head_lemma, "noun")

    # get all phrase head synsets that have a synset of the paraphrase head as their hypernym
    phrase_head_synsets_with_paraphrase_head_as_hypernym = [syn for syn in phrase_head_synsets if not set(GLOBAL_WORDNET_INTERFACE.get_hypernym_synsets(syn, traversal_depth=3)).isdisjoint(paraphrase_head_synsets)]

    if phrase_head_synsets_with_paraphrase_head_as_hypernym:
        pass
        # print("The phrase '{0}' has a potential paraphrase '{1}', that is its hypernym!".format(phrase_head_lemma, paraphrase_head_lemma))
    else:
        return specifies_with_attributes

    # for each phrase head synset with a paraphrase head synset as an hypernym check if that phrase synsets attributes have an intersection with the adjectives that modify the paraphrase head
    poss_matches = [0 for i in phrase_head_synsets_with_paraphrase_head_as_hypernym]
    for i, phrase_head_synset_with_hypernym in enumerate(phrase_head_synsets_with_paraphrase_head_as_hypernym):
        if "attributes" not in phrase_head_synset_with_hypernym.relations.keys(): continue
        attributes_synsets = [GLOBAL_WORDNET_INTERFACE.synset_from_id(syn_id) for syn_id in phrase_head_synset_with_hypernym.relations["attributes"] if GLOBAL_WORDNET_INTERFACE.synset_from_id(syn_id).ss_type in "as"]
        attributes_ids_extended = set([syn.synset_id for syn in list(itertools.chain(*[GLOBAL_WORDNET_INTERFACE.get_similar_adjectives(syn) for syn in attributes_synsets])) + attributes_synsets])
        for attr in attributes_ids_extended:
            if attr in paraphrase_head_adjectives_synset_ids:
                poss_matches[i] += 1

    attribute_matches = max(poss_matches)
    if attribute_matches > 0:
        specifies_with_attributes = True

    return specifies_with_attributes
