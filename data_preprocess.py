from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

RANDOM_STATE = 42
TEST_SIZE = 0.15

RAW_DATA_PATH = Path("data/raw/dialog_acts.dat")
PROCESSED_DIR = Path("data/processed")

def load_dialog_acts(file_path):
    data = []

    with open(file_path, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()

            if not line:
                continue

            act, utterance = line.split(maxsplit=1)

            data.append({"act": act.lower(), "utterance": utterance.lower()})

    return pd.DataFrame(data)

def save_split(df, file_path):
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, "w", encoding="utf-8") as file:
        for _, row in df.iterrows():
            file.write(f"{row['act']} {row['utterance']}\n")

def create_split_original(df):
    train_df, test_df = train_test_split(df, test_size=TEST_SIZE, random_state= RANDOM_STATE, stratify = df["act"])

    return train_df, test_df

def create_split_grouped(df):
    grouped = (
        df.groupby("utterance")["act"]
        .agg(lambda labels: labels.value_counts().idxmax())
        .reset_index()
    )

    try:
        train_groups, test_groups = train_test_split(
            grouped,
            test_size=TEST_SIZE,
            random_state=RANDOM_STATE,
            stratify=grouped["act"]
        )
    except ValueError:
        print("Stratified grouped split was not possible because at least one class has too few unique utterances.")
        print("Using grouped split without stratification instead.")

        train_groups, test_groups = train_test_split(
            grouped,
            test_size=TEST_SIZE,
            random_state=RANDOM_STATE
        )

    train_utterances= set(train_groups["utterance"])
    test_utterances= set(test_groups["utterance"])

    train_df= df[df["utterance"].isin(train_utterances)]
    test_df= df[df["utterance"].isin(test_utterances)]

    return train_df, test_df

def process():
    df = load_dialog_acts(RAW_DATA_PATH)

    original_train, original_test = create_split_original(df)
    grouped_train, grouped_test = create_split_grouped(df)

    save_split(original_train, PROCESSED_DIR / "original_train.dat")
    save_split(original_test, PROCESSED_DIR / "original_test.dat")
    save_split(grouped_train, PROCESSED_DIR / "grouped_train.dat")
    save_split(grouped_test, PROCESSED_DIR / "grouped_test.dat")

    print("Data preprocessing completed.")
    print(f"Full dataset: {len(df)} examples")
    print(f"Original train set: {len(original_train)} examples")
    print(f"Original test set: {len(original_test)} examples")
    print(f"Grouped train set: {len(grouped_train)} examples")
    print(f"Grouped test set: {len(grouped_test)} examples")

    overlap = set(grouped_train["utterance"]) & set(grouped_test["utterance"])
    print(f"Overlap between grouped train and test sets: {len(overlap)}")

if __name__ == "__main__":
    process()

