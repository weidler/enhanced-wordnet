python3 src/coref/train_coref.py -in data/conll-2012/conll_files/train/cctv_0001.v4_auto_conll -out test.obj -extractor cort.coreference.approaches.mention_ranking.extract_substructures -perceptron cort.coreference.approaches.mention_ranking.RankingPerceptron -cost_function cort.coreference.cost_functions.cost_based_on_consistency -features features_test.txt
