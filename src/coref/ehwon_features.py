"""Additional Cort Features based on Enhanced WordNet."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), "../../"))

import random as ran

def random_feature(mention):
    """random test."""
    return "fine_type", ran.randint(0, 10)

def antecedent_attribute_congruency(anaphor, antecedent):
    """Compute the congruency between the antecedents EhWoN attributes and the anaphors adjectival modifiers."""
    pass

def anaphor_attribute_congruency(anaphor, antecedent):
    """Compute the congruency between the anaphors EhWoN attributes and the antecedents adjectival modifiers."""
    pass

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

def antecedent_performs_anaphor_application(anaphor, antecedent):
    """Compute whether the antecedent is object of a verb that is the anaphors application."""
