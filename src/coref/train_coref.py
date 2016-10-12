#!/usr/bin/env python3

"""Shameless copy of the cort script simply to add the path inserter... Could have been
solved a bit more elegant."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), "../../"))

import argparse
import codecs
import logging
import pickle
from pprint import pprint

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(''message)s')

from cort.core import corpora
from cort.core import mention_extractor
from cort.coreference import experiments
from cort.coreference import features
from cort.coreference import instance_extractors
from cort.util import import_helper

def parse_args():
    parser = argparse.ArgumentParser(description='Train coreference resolution models.')

    parser.add_argument('-in',
                        required=True,
                        dest='input_filename',
                        help='The input file. Must follow the format of the '
                            'CoNLL shared tasks on coreference resolution '
                            '(see http://conll.cemantix.org/2012/data.html).)')
    parser.add_argument('-out',
                        dest='output_filename',
                        required=True,
                        help='The output file the learned model will be saved '
                            'to.')
    parser.add_argument('-extractor',
                        dest='extractor',
                        required=True,
                        help='The function to extract instances.')
    parser.add_argument('-perceptron',
                        dest='perceptron',
                        required=True,
                        help='The perceptron to use.')
    parser.add_argument('-cost_function',
                        dest='cost_function',
                        required=True,
                        help='The cost function to use.')
    parser.add_argument('-n_iter',
                        dest='n_iter',
                        default=5,
                        help='Number of perceptron iterations. Defaults to 5.')
    parser.add_argument('-cost_scaling',
                        dest='cost_scaling',
                        default=1,
                        help='Scaling factor of the cost function. Defaults '
                            'to 1')
    parser.add_argument('-random_seed',
                        dest='seed',
                        default=23,
                        help='Random seed for training data shuffling. '
                            'Defaults to 23.')
    parser.add_argument('-features',
                        dest='features',
                        help='The file containing the list of features. If not'
                            'provided, defaults to a standard set of'
                            'features.')

    return parser.parse_args()


if sys.version_info[0] == 2:
    logging.warning("You are running cort under Python 2. cort is much more "
                    "efficient under Python 3.3+.")

args = parse_args()

if args.features:
    print("reading features...")
    mention_features, pairwise_features = import_helper.get_features(
        args.features)
else:
    mention_features = [
        features.fine_type,
        features.gender,
        features.number,
        features.sem_class,
        features.deprel,
        features.head_ner,
        features.length,
        features.head,
        features.first,
        features.last,
        features.preceding_token,
        features.next_token,
        features.governor,
        features.ancestry
    ]

    pairwise_features = [
        features.exact_match,
        features.head_match,
        features.same_speaker,
        features.alias,
        features.sentence_distance,
        features.embedding,
        features.modifier,
        features.tokens_contained,
        features.head_contained,
        features.token_distance
    ]


perceptron = import_helper.import_from_path(args.perceptron)(
    cost_scaling=int(args.cost_scaling),
    n_iter=int(args.n_iter),
    seed=int(args.seed)
)

extractor = instance_extractors.InstanceExtractor(
    import_helper.import_from_path(args.extractor),
    mention_features,
    pairwise_features,
    import_helper.import_from_path(args.cost_function),
    perceptron.get_labels()
)

logging.info("Reading in data.")
training_corpus = corpora.Corpus.from_file("training",
                                        codecs.open(args.input_filename,
                                                    "r", "utf-8"))

logging.info("Extracting system mentions.")
for doc in training_corpus:
    doc.system_mentions = mention_extractor.extract_system_mentions(doc)

model = experiments.learn(
    training_corpus,
    extractor,
    perceptron
)

logging.info("Writing model to file.")
pickle.dump(model, open(args.output_filename, "wb"), protocol=2)

logging.info("Done.")
