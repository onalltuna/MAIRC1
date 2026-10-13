#for now this is the chat window from my intelligent agents project, but we can tweak it:
# delete one mode, and make it reasoning mode vs no reasoning mode
# in and output from system/user can go though this widnow
# delete ontology mode button haha not relevant here
# -Noor

import tkinter as tk
from tkinter import scrolledtext


def get_response(message):
    """does nothing for now, need to change to actual output from llm"""
    mode = mode_var.get()
    if mode == "baseline":
        return "(placeholder baseline) You said: " + message
    elif mode == "agent_no_ontology":
        return "(placeholder agent, ontology OFF) You said: " + message
    else:
        return "(placeholder agent, ontology ON) You said: " + message

def send(event=None):
    message = entry.get().strip()
    if not message:
        return
    entry.delete(0, tk.END)
    output.insert(tk.END, "You: " + message + "\n")
    output.insert(tk.END, "Assistant: " + get_response(message) + "\n\n")
    output.see(tk.END)

root = tk.Tk()
root.title("IntelligentAgents LLM Chat")

# Mode selection at the top of the screen
mode_var = tk.StringVar(value="baseline")


def on_mode_change():
    global is_on
    mode = mode_var.get()
    if mode == "baseline":
        # baseline does not use the ontology (or the agent)
        toggle_btn.config(text="Ontology mode: N/A", bg="gray", fg="black")
        is_on = False
    elif mode == "agent_ontology":
        toggle_btn.config(text="Ontology mode: ON", bg="green", fg="white")
        is_on = True
    elif mode == "agent_no_ontology":
        toggle_btn.config(text="Ontology mode: OFF", bg="red", fg="white")
        is_on = False


mode_frame = tk.LabelFrame(root, text="Mode")
mode_frame.pack(side="top", fill=tk.X, padx=10, pady=(10, 0))
tk.Radiobutton(
    mode_frame, text="Baseline LLM", variable=mode_var,
    value="baseline", command=on_mode_change, anchor="w"
).pack(fill=tk.X, padx=5)
tk.Radiobutton(
    mode_frame, text="Agent without ontology", variable=mode_var,
    value="agent_no_ontology", command=on_mode_change, anchor="w"
).pack(fill=tk.X, padx=5)
tk.Radiobutton(
    mode_frame, text="Agent with ontology", variable=mode_var,
    value="agent_ontology", command=on_mode_change, anchor="w"
).pack(fill=tk.X, padx=5)

output = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=60, height=20)
output.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

entry = tk.Entry(root)
entry.pack(side=tk.LEFT, padx=10, pady=(0, 10), fill=tk.X, expand=True)
entry.bind("<Return>", send)

tk.Button(root, text="Send", command=send).pack(side=tk.RIGHT, padx=10, pady=(0, 10))


is_on = False


def toggle_mode():
    global is_on
    if is_on:
        toggle_btn.config(text="Ontology mode: OFF", bg="red", fg="white")
        is_on = False
    else:
        toggle_btn.config(text="Ontology mode: ON", bg="green", fg="white")
        is_on = True



toggle_btn = tk.Button(
    root, 
    text="Ontology mode: N/A", 
    bg="gray", 
    fg="white", 
    font=("Arial", 12), 
    command=toggle_mode,
    state="disabled",  # indicator only, controlled by the mode selection above
    disabledforeground="white"
)

toggle_btn.pack(side="bottom", pady=20)

root.mainloop()