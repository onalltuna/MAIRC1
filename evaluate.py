import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score, confusion_matrix


def evaluate(df, general_file_name=None, conf_matrix_name=None):
    y_true = df["act"]
    y_pred = df["pred"]

    accuracy = accuracy_score(y_true, y_pred)
    balanced_accuracy = balanced_accuracy_score(y_true, y_pred)
    macro_f1 = f1_score(y_true, y_pred, average="macro")

    print(f"Accuracy: {accuracy}")
    print(f"Balanced Accuracy: {balanced_accuracy}")
    print(f"Macro F1: {macro_f1:.4f}")

    incorrect_mask = y_true != y_pred
    incorrect_counts = y_true[incorrect_mask].value_counts().sort_values(ascending=False)

    os.makedirs("results", exist_ok=True)

    fig = plt.figure(figsize=(9, 7), constrained_layout=True)
    gs = gridspec.GridSpec(2, 1, height_ratios=[1, 3], figure=fig)

    ax_text = fig.add_subplot(gs[0])
    ax_text.axis("off")
    metrics_text = (
        f"Accuracy:          {accuracy:.4f}\n"
        f"Balanced Accuracy: {balanced_accuracy:.4f}\n"
        f"Macro F1:          {macro_f1:.4f}"
    )
    ax_text.text(
        0.01, 0.5, metrics_text,
        fontsize=13, fontfamily="monospace",
        va="center", ha="left",
    )
    ax_text.set_title("Number of False Predictions per Class", fontsize=14, fontweight="bold", loc="left")

    ax_bar = fig.add_subplot(gs[1])
    if len(incorrect_counts) > 0:
        ax_bar.bar(incorrect_counts.index, incorrect_counts.values, color="indianred")
        ax_bar.set_ylabel("Number of incorrect predictions")
        ax_bar.set_xlabel("Dialog act (true label)")
        ax_bar.set_title("Incorrect predictions per dialog act")
        ax_bar.tick_params(axis="x", rotation=45)
        for i, v in enumerate(incorrect_counts.values):
            ax_bar.text(i, v, str(v), ha="center", va="bottom", fontsize=9)
    else:
        ax_bar.text(0.5, 0.5, "No incorrect predictions", ha="center", va="center", fontsize=12)
        ax_bar.axis("off")

    path = "results/" + general_file_name
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Evaluation figure saved to {path}")

    labels = sorted(pd.unique(pd.concat([y_true, y_pred])))
    cm = confusion_matrix(y_true, y_pred, labels=labels)

    n_labels = len(labels)
    fig_cm, ax_cm = plt.subplots(
        figsize=(max(6, n_labels * 0.6), max(5, n_labels * 0.6)),
        constrained_layout=True,
    )
    im = ax_cm.imshow(cm, cmap="Blues")

    ax_cm.set_xticks(range(n_labels))
    ax_cm.set_yticks(range(n_labels))
    ax_cm.set_xticklabels(labels, rotation=45, ha="right")
    ax_cm.set_yticklabels(labels)
    ax_cm.set_xlabel("Predicted act")
    ax_cm.set_ylabel("True act")

    # annotate each cell with its count
    thresh = cm.max() / 2 if cm.max() > 0 else 0
    for i in range(n_labels):
        for j in range(n_labels):
            value = cm[i, j]
            if value > 0:
                ax_cm.text(
                    j, i, str(value),
                    ha="center", va="center",
                    fontsize=8,
                    color="white" if value > thresh else "black",
                )

    fig_cm.colorbar(im, ax=ax_cm, fraction=0.046, pad=0.04)

    path = "results/" + conf_matrix_name
    fig_cm.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig_cm)
    print(f"Confusion matrix saved to {path}")
