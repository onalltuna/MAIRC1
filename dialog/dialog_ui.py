import tkinter as tk
from tkinter import scrolledtext, messagebox

from dialog.dialog_manager_test import DialogSession


def launch_dialog_ui(
    is_grouped=True,
    use_bert=True,
    slot_fallback="levenshtein",
):
    # ==========================================
    # Setup window: name and transparency
    # ==========================================

    setup = tk.Tk()
    setup.title("Restaurant Dialog System - Setup")
    setup.geometry("420x300")
    setup.resizable(False, False)

    tk.Label(
        setup,
        text="Welcome to the Restaurant Dialog System",
        font=("Arial", 14, "bold"),
        wraplength=380,
    ).pack(padx=20, pady=(20, 15))

    # User name
    tk.Label(
        setup,
        text="What is your name?",
        font=("Arial", 11),
    ).pack(anchor="w", padx=30)

    name_var = tk.StringVar()

    name_entry = tk.Entry(
        setup,
        textvariable=name_var,
        font=("Arial", 11),
        width=35,
    )
    name_entry.pack(padx=30, pady=(5, 15))
    name_entry.focus_set()

    # Transparency selection
    tk.Label(
        setup,
        text="Enable reasoning transparency?",
        font=("Arial", 11),
    ).pack(anchor="w", padx=30)

    transparency_var = tk.StringVar(value="y")

    transparency_frame = tk.Frame(setup)
    transparency_frame.pack(anchor="w", padx=25, pady=5)

    tk.Radiobutton(
        transparency_frame,
        text="Yes",
        variable=transparency_var,
        value="y",
    ).pack(side=tk.LEFT, padx=5)

    tk.Radiobutton(
        transparency_frame,
        text="No",
        variable=transparency_var,
        value="n",
    ).pack(side=tk.LEFT, padx=15)

    # Store the setup choices here.
    user_settings = {}

    def start_chat(event=None):
        name = name_var.get().strip()

        if not name:
            messagebox.showwarning(
                "Name Required",
                "Please enter your name before starting the chat.",
                parent=setup,
            )
            name_entry.focus_set()
            return

        user_settings["name"] = name
        user_settings["reasoning_transparency"] = (
            transparency_var.get() == "y"
        )

        setup.destroy()

    tk.Button(
        setup,
        text="Start Chat",
        command=start_chat,
        font=("Arial", 11, "bold"),
        width=15,
    ).pack(pady=15)

    name_entry.bind("<Return>", start_chat)

    setup.mainloop()

    # If the user closes the setup window instead of starting,
    # don't launch the chat.
    if not user_settings:
        return

    user_name = user_settings["name"]
    reasoning_transparency = user_settings["reasoning_transparency"]

    # ==========================================
    # Chat window
    # ==========================================

    root = tk.Tk()
    root.title(f"Restaurant Dialog System - {user_name}")
    root.geometry("750x650")
    root.minsize(550, 450)

    # TTS is always disabled.
    session = DialogSession(
        is_grouped=is_grouped,
        use_bert=use_bert,
        slot_fallback=slot_fallback,
        reasoning_transparency=reasoning_transparency,
        tts=False,
        user_name=user_name,
    )

    # Chat history
    output = scrolledtext.ScrolledText(
        root,
        wrap=tk.WORD,
        height=25,
        state=tk.DISABLED,
        font=("Arial", 11),
    )
    output.pack(
        padx=10,
        pady=10,
        fill=tk.BOTH,
        expand=True,
    )

    def append_message(sender, message):
        output.config(state=tk.NORMAL)
        output.insert(tk.END, f"{sender}: {message}\n\n")
        output.config(state=tk.DISABLED)
        output.see(tk.END)

    # Personalized welcome message
    append_message(
        "Assistant",
        f"Hello {user_name}! {session.welcome_response}",
    )

    # User input
    input_frame = tk.Frame(root)
    input_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

    entry = tk.Entry(input_frame, font=("Arial", 11))
    entry.pack(
        side=tk.LEFT,
        fill=tk.X,
        expand=True,
        padx=(0, 10),
    )
    entry.focus_set()

    def send(event=None):
        message = entry.get().strip()

        if not message:
            return "break"

        entry.delete(0, tk.END)
        append_message(user_name, message)

        try:
            system_response, finished = session.process_message(message)

            if system_response:
                append_message("Assistant", system_response)

            if finished:
                entry.config(state=tk.DISABLED)
                send_button.config(state=tk.DISABLED)

        except Exception as exc:
            messagebox.showerror(
                "Dialog Error",
                f"Could not process the message:\n{exc}",
                parent=root,
            )

        entry.focus_set()
        return "break"

    entry.bind("<Return>", send)

    send_button = tk.Button(
        input_frame,
        text="Send",
        command=send,
    )
    send_button.pack(side=tk.RIGHT)

    def on_close():
        session.close()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)

    root.mainloop()