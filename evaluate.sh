# Wrapper for the evaluation process

RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

ACTION="$1"  # all, train, test, score
shift
POSSIBLE_ACTIONS=("all" "train" "test" "score")

action_known=false
for item in "${POSSIBLE_ACTIONS[@]}"; do
	[[ $ACTION == "$item" ]] && action_known=true
done

if [[ $action_known = false ]]; then
	echo "unknown action";
	exit 0
fi

TRAINING_SET="dev";
TEST_SET="test";
FEATURE_SET="ehwon";

while getopts t:p:f: opt; do
	case $opt in
		t)
			TRAINING_SET=$OPTARG
			;;
		p)
			TEST_SET=$OPTARG
			;;
		f)
			FEATURE_SET=$OPTARG
			;;
	esac
done

TRAINING_FILE="data/conll-2012/"$TRAINING_SET".auto";
MODEL="models/"$TRAINING_SET"_"$FEATURE_SET"_model.obj";
TEST_FILE="data/conll-2012/"$TEST_SET".gold";
FEATURE_FILE="features_"$FEATURE_SET".txt";
PREDICTION_OUTPUT_FILE=$FEATURE_SET"_out.conll";

printf $BLUE"\nInititializing procedure..."

if [[ $ACTION = "train" ]] || [[ $ACTION = "all" ]]; then
	printf $NC"\n\ntraining model "$RED$MODEL$NC"\nbased on features in "$RED$FEATURE_FILE$NC"\ncalculated for data set "$RED$TRAINING_FILE$NC"\n\n"
	python3 src/coref/train_coref.py -in $TRAINING_FILE -out $MODEL -extractor cort.coreference.approaches.mention_ranking.extract_substructures -perceptron cort.coreference.approaches.mention_ranking.RankingPerceptron -cost_function cort.coreference.cost_functions.cost_based_on_consistency -features $FEATURE_FILE
fi

if [[ $ACTION = "test" ]] || [[ $ACTION = "all" ]]; then
	printf "\n\ntesting with model "$RED$MODEL$NC" \nbased on features in "$RED$FEATURE_FILE$NC" \ncalculated for test set "$RED$TEST_FILE$NC" \ncreating "$RED$PREDICTION_OUTPUT_FILE$NC"\n\n"
	python3 src/coref/predict_coref.py -in $TEST_FILE -model $MODEL -out $PREDICTION_OUTPUT_FILE -extractor cort.coreference.approaches.mention_ranking.extract_substructures -perceptron cort.coreference.approaches.mention_ranking.RankingPerceptron -clusterer cort.coreference.clusterer.all_ante -features $FEATURE_FILE
fi

if [[ $ACTION = "score" ]] || [[ $ACTION = "all" ]]; then
	printf "\n\nevaluating the output file "$RED$PREDICTION_OUTPUT_FILE$NC" \nagainst test file "$RED$TEST_FILE$NC"\n\n"
	perl src/tools/reference-coreference-scorers-master/scorer.pl all $TEST_FILE $PREDICTION_OUTPUT_FILE none
fi
