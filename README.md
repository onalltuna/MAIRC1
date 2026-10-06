# Restaurant Dialog System

## About

This project implements a restaurant recommendation dialog system in two parts. **Part 1** focuses on dialog act classification: utterances in a conversation are actions (greeting, asking, confirming, and so on). We implement, train, and compare different classifiers for this task: a manually constructed rule-based baseline built from keyword matching, and two machine learning classifiers — a multi-layer perceptron (`ml1`) and logistic regression (`ml2`) — each trained on two different feature representations: bag-of-words and frozen pretrained DistilBERT embeddings. This gives four ML model variants in total, letting us compare representation choices while holding the classifier algorithm fixed.

**Part 2** builds on this by combining the Part 1 classifier with slot extraction, restaurant lookup, reasoning, and natural language response generation into a complete dialog manager. The system runs in the terminal and holds a full conversation with the user, using the classifier from Part 1 to route every user utterance to the correct dialog act before deciding how to respond, ultimately aiming to recommend a restaurant that matches the user's stated preferences.



## Project structure

```
.
├── main.py                     # CLI entry point (train / test / prompt / dialog / heldout)
├── data_preprocess.py          # Generates processed train/test splits from raw data
├── classifiers/
│   ├── bert_encoder.py
│   ├── rule_based.py           # Keyword-matching baseline
│   ├── ml_classifier_1.py      # ml1 — MLP (BoW and DistilBERT variants)
│   └── ml_classifier_2.py      # ml2 — Logistic Regression (BoW and DistilBERT variants)  
├── dialog/
│   ├── dialog_manager.py       # Full terminal-based dialog system (Part 1b)
│   ├── ontology.py
│   ├── reasoning.py
│   ├── response_generator.py
│   ├── responses.py
│   ├── restaurant_info_extenden.csv
│   ├── restaurant_lookup.py
│   ├── semantic_similarity.py
│   ├── slot_extractor.py
│   ├── state.py
│   ├── transition.py
├── prompt.py                   # Prompt-based single-utterance classification interface
├── evaluate.py                
├── data/
│   ├── raw/                    # Raw dataset + held-out test file
│   └── processed/              # Original and grouped train/test splits
```



## Data Preprocessing

The raw DSTC 2 dialog acts data is stored in 'data/raw/dialog_acts.dat'. Each line contains a dialog acts label followed by the corresponding user utterance. The preprocessing script reads this file line by line,seperates the label from the utterance and converts them both to lowercase.
### Splitting strategy

Many utterances in the dataset are not uniwue. With a normal random split, the same utterance may appear in both training and test data, which can cause data leakage. 
Therefore, we create two split variants:

- **Original split** (`--grouped n`) - a stratified random 85/15 train-test split over all utterance instances. Duplicate utterances may occur in both train and test.
- **Grouped split** (`--grouped y`) - an 85/15 split over unique utterance groups, where identical utterances are kept in the same split. Stratified sampling is applied where possible. The `reqmore` class has only one unique utterance group (`more`), so it is assigned to the training set and excluded from the stratified group-level split.

### Processed data

The processed train/test files for both split variants are already included under `data/processed/`. If you want to regenerate them from scratch, run:

```bash
python data_preprocess.py
```

On Windows, if `python` is not recognized, use: 

```powershell
py data_preprocess.py
```

## Requirements

* Python 3
* uv — Python package manager. Check the [uv installation guide](https://docs.astral.sh/uv/#installation) for installation instructions.
* venv (included with standard Python installations)

## Create and activate the Virtual Environment

### macOS / Linux

```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

### Windows

```powershell
uv venv
.\.venv\Scripts\Activate.ps1
uv pip install -r requirements.txt
```

## How to run

```bash
python main.py train --classifier <name> --grouped <y/n> [--bert <y/n>]
python main.py test --classifier <name> --grouped <y/n> [--bert <y/n>]
python main.py prompt --classifier <name> --grouped <y/n> [--bert <y/n>]
python main.py dialog --grouped <y/n> [--reasoning-transparency <y/n>] [--bert <y/n>]
python main.py heldout --classifier <name> --grouped <y/n> [--bert <y/n>]
```

> **Note:** `train` must be run for a given `--classifier`/`--grouped`/`--bert` combination before `test`, `prompt`, `dialog`, or `heldout` can be used with that same combination — those commands load the model file that `train` produces. Running them first will print a clear error telling you which `train` command to run.

#### `train`
Runs the training process for the selected classifier.

#### `test`
Runs the testing process for the selected classifier.

#### `prompt`
Starts a prompt-based classification interface: the user enters an utterance and the system prints the predicted dialog act using the selected classifier. This repeats until the user exits by typing `/exit` or pressing Ctrl+C.

#### `dialog`
Starts the full restaurant dialog system: a working, terminal-based dialog manager that holds an actual conversation with the user and recommends a restaurant. User can exit the dialog system by typing /exit or pressing Ctrl+C. Users can also enable additional accessibility features such as reasoning transparency and Text to Speech that are described below.

#### `heldout`
Loads the held-out test set and applies testing on that file. For this command to be usable, the held-out data file needs to be stored at `data/raw/dialog_acts_test.dat`.

#### Allowed classifier names

- `rulebased` — keyword-matching baseline
- `ml1` — MLP (multi-layer perceptron)
- `ml2` — Logistic Regression

#### Allowed group options

- `y`
- `n`

### `--bert`

Controls which feature representation is used for the ML classifiers (`ml1` and `ml2`). It is optional, and defaults to `n`.

- `--bert n` (or omitting the flag) — utterances are represented using **bag-of-words (BoW)**. This is the default behavior: the classifier is trained/tested on sparse word-count vectors built from the training vocabulary.
- `--bert y` — utterances are represented using **frozen pretrained DistilBERT embeddings** instead. Each utterance is encoded into a fixed-size dense vector using DistilBERT as a feature extractor (no fine-tuning), and the classifier is trained/tested on those embeddings.

Note that `--bert` only applies to `ml1` and `ml2` — it has no effect on `rulebased`, since the rule-based classifier does not use a learned feature representation at all.

### `--reasoning-transparency`

Controls whether the dialog system gives an explanation behind the answers of the system.

- `--reasoning-transparency y` — shows the explanation of the reasoning. This is the default.
- `--reasoning-transparency n` — hides the reasoning explanation and only gives the answer (recommendation).

This option implements the configurable feature for part 2. The reasoning transparency can be switched on or off while keeping the rest of the dialog system the same.

### `--tts`

Controls whether the Text to Speech is enabled for the dialog system.

- `--tts y` — The system reads the system messages out loud so the user can hear the system messages.
- `--tts n` — Text to Speech is not enabled and the system messages are only printed on the terminal.

### Example: running BoW + a classifier

To explicitly run with bag-of-words features, add `--bert n` (or simply leave `--bert` out, since `n` is the default):

```bash
# these two are equivalent
python main.py train --classifier ml1 --grouped n --bert n
python main.py train --classifier ml1 --grouped n

python main.py test --classifier ml2 --grouped y --bert n
python main.py test --classifier ml2 --grouped y
```

### General Usage Examples

```bash
python main.py train --classifier rulebased --grouped n
python main.py test --classifier ml1 --grouped y --bert y
python main.py prompt --classifier ml1 --grouped y --bert y
python main.py dialog --grouped y --bert n --reasoning-transparency y --tts y
python main.py dialog --grouped y --bert n --reasoning-transparency n
python main.py heldout --classifier rulebased --grouped n --bert n
```