# Restaurant Dialog System

## About

This project implements a restaurant recommendation dialog system in two parts. **Part 1** focuses on dialog act classification: utterances in a conversation are actions (greeting, asking, confirming, and so on). We implement, train, and compare different classifiers for classifying conversation actions task: a manually constructed rule-based baseline built from keyword matching, and two machine learning classifiers — a multi-layer perceptron (`ml1`) and logistic regression (`ml2`) — each trained on two different feature representations: bag-of-words and frozen pretrained DistilBERT embeddings. This gives four ML model variants in total, letting us compare representation choices while holding the classifier algorithm fixed.

**Part 1** builds on this by combining the Part 1 classifier with slot extraction, restaurant lookup, reasoning, and natural language response generation into a complete dialog manager. The system runs in the terminal and holds a full conversation with the user, using the classifier from Part 1 to route every user utterance to the correct dialog act before deciding how to respond, ultimately aims to recommend a restaurant that matches the user's stated preferences.

## Data Preprocessing

### Splitting strategy

Many utterances in the dataset are not unique and with a naive random train/test split, this can cause **data leakage**: the same utterance may end up in both the training and test sets, letting a model "recognize" a sentence it has effectively already seen rather than genuinely generalizing to unseen input. This would inflate test accuracy and give a misleading picture of real performance.

To address this, every ML classifier is trained and evaluated on **two split variants**, controlled by the `--grouped` flag:

- **Original split** (`--grouped n`) — a random 85/15 train/test split over the full dataset. Duplicate utterances may end up on both sides of the split.
- **Grouped split** (`--grouped y`) — an 85/15 split where all duplicate utterances are kept together in the same split (either entirely in train or entirely in test).

Both splits use **stratified sampling**, so the class (dialog act) distribution in the test set matches the distribution in the training set. 

### Processed data

The processed train/test files for both split variants are already included under `data/processed/`. If you want to regenerate them from scratch run:

```bash
python data_preprocess.py
```

## Requirements

* Python 3
* uv — Python package manager. Check the [uv installation guide](https://docs.astral.sh/uv/#installation) for installation instructions.
* venv (included with standard Python installations)

## Create and activate the Virtual Enviroment

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
python main.py dialog --classifier <name>
python main.py heldout --classifier <name> --grouped <y/n> [--bert <y/n>]
```

#### `train`
Runs the training process for the selected classifier.

#### `test`
Runs the testing process for the selected classifier.

#### `prompt`
Starts a prompt-based classification interface: the user enters an utterance and the system prints the predicted dialog act using the selected classifier, repeating until the user exits.

#### `dialog`
Starts the full restaurant dialog system: a working, terminal-based dialog manager that holds an actual conversation with the user and recommends a restaurant.

#### `heldout`
Loads the held-out test set and applies testing on that file. For this command to be usable, the held-out data file needs to be stored at `data/raw/dialog_acts_test.dat`.

#### Allowed classifier names

- `rulebased` — keyword-matching baseline
- `ml1` - MLP (multi-layer perceptron)
- `ml2` — Logistic Regression

#### Allowed group options

- `y`
- `n`

### `--bert`

Controls which feature representation is used for the ML classifiers (`ml1` and `ml2`). It is optional, and defaults to `n`.

- `--bert n` (or omitting the flag) — utterances are represented using **bag-of-words (BoW)**. This is the default behavior: the classifier is trained/tested on sparse word-count vectors built from the training vocabulary.
- `--bert y` — utterances are represented using **frozen pretrained DistilBERT embeddings** instead. Each utterance is encoded into a fixed-size dense vector using DistilBERT as a feature extractor (no fine-tuning), and the classifier is trained/tested on those embeddings.

Note that `--bert` only applies to `ml1` and `ml2` — it has no effect on `rulebased`, since the rule-based classifier does not use a learned feature representation at all.

### Example: running BoW + a classifier

To explicitly run with bag-of-words features, add `--bert n` (or simply leave `--bert` out, since `n` is the default):


### General Usage Examples

```bash
python main.py train --classifier rulebased --grouped n
python main.py test --classifier ml1 --grouped y --bert y
python main.py prompt --classifier ml1 --grouped y --bert y
python main.py dialog --classifier ml2
python main.py heldout --classifier rulebased --grouped n --bert n
```
