import tkinter as tk
from tkinter import messagebox
import random

letters = 'abcdefghijklmnopqrstuvwxyz'
numbers = '1234567890'
symbols = '!@#$%^&*()-=_+'

def char_type(ch):
    if ch.islower() or ch.isupper():
        return 'letter'
    elif ch.isdigit():
        return 'number'
    else:
        return 'symbol'

def check_strength(password):
    """Evaluate password strength and return a tuple:
    (label, score, secure_bool)

    New rules:
    - Require presence of upper, lower, digit and symbol and min length 8 to be considered secure.
    - Give more weight to digits/symbols and longer lengths.
    - Penalize repeated characters and obvious sequences.
    - Return a descriptive label: 'Strong', 'Moderate', or 'Weak'.
    """
    score = 0
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_symbol = any(c in symbols for c in password)
    length = len(password)

    # Base scoring (higher is better)
    score += 2 if has_upper else 0
    score += 2 if has_lower else 0
    score += 3 if has_digit else 0
    score += 3 if has_symbol else 0
    score += 2 if length >= 12 else (1 if length >= 8 else 0)

    # Penalty for repeated characters
    if password:
        max_repeat = max(password.count(ch) for ch in set(password))
        if max_repeat > 2:
            score -= (max_repeat - 2)

    # Penalty for simple sequential runs (abc, 123, cba, 321)
    seq_penalty = 0
    lower = password.lower()
    for i in range(len(lower) - 2):
        seg = lower[i:i+3]
        if len(seg) < 3:
            continue
        # check ascending or descending sequences
        if all(ord(seg[j+1]) - ord(seg[j]) == 1 for j in range(2)) or all(ord(seg[j]) - ord(seg[j+1]) == 1 for j in range(2)):
            seq_penalty += 1
    score -= seq_penalty

    # Determine whether it's secure by stricter criteria
    secure = all([has_upper, has_lower, has_digit, has_symbol, length >= 8]) and score >= 7

    if secure:
        label = "Strong"
    elif score >= 5:
        label = "Moderate"
    else:
        label = "Weak"

    return (label, score, secure)

def generate_passwords(length=8, quantity=1,
                       allow_letters=True, custom_letters="",
                       allow_numbers=True, custom_numbers="",
                       allow_symbols=True, custom_symbols="",
                       allow_uppercases=True,
                       unsl=False):
    letters_set = custom_letters if (allow_letters and custom_letters) else (letters if allow_letters else "")
    numbers_set = custom_numbers if (allow_numbers and custom_numbers) else (numbers if allow_numbers else "")
    symbols_set = custom_symbols if (allow_symbols and custom_symbols) else (symbols if allow_symbols else "")
    upper_set   = letters_set.upper() if allow_uppercases and letters_set else ""

    allowed_keywords = letters_set + numbers_set + symbols_set + upper_set
    if not allowed_keywords:
        raise ValueError("No characters allowed!")

    passwords = []
    attempts = 0
    while len(passwords) < quantity and attempts < quantity * 10:
        attempts += 1
        password = ''
        used_types = set()

        if unsl:
            if upper_set: 
                password += random.choice(upper_set); used_types.add('letter')
            if numbers_set: 
                password += random.choice(numbers_set); used_types.add('number')
            if symbols_set: 
                password += random.choice(symbols_set); used_types.add('symbol')
            if letters_set: 
                password += random.choice(letters_set); used_types.add('letter')

            while len(password) < length:
                ch = random.choice(allowed_keywords)
                if char_type(ch) != char_type(password[-1]):
                    password += ch
                    used_types.add(char_type(ch))
        else:
            while len(password) < length:
                ch = random.choice(allowed_keywords)
                if len(password) == 0 or char_type(ch) != char_type(password[-1]):
                    password += ch
                    used_types.add(char_type(ch))

        # For very short passwords (< 4), accept if at least 2 types are used; otherwise require all 3
        min_types = 2 if length < 4 else 3
        if len(used_types) >= min_types:
            passwords.append((password, check_strength(password)))
        else:
            messagebox.showerror("Generation Error", "Failed to generate password with required password length. Please adjust settings.")
            return ['Failed to generate']

    return passwords

def main():
    root = tk.Tk()
    root.title("Password Generator")
    root.geometry("700x600")

    main_menu_frame = tk.Frame(root, bg="lightblue")
    generator_frame = tk.Frame(root, bg="lightgreen")

    tk.Label(main_menu_frame, text="Welcome to Password Generator",
             font=("Arial", 24, "bold"), bg="lightblue").pack(pady=40)
    tk.Button(main_menu_frame, text="Get Started!", font=("Arial", 16),
              command=lambda: switch_menu(main_menu_frame, generator_frame)).pack(pady=20)

    length_var = tk.IntVar(value=12)
    quantity_var = tk.IntVar(value=3)
    allow_letters = tk.BooleanVar(value=True)
    allow_numbers = tk.BooleanVar(value=True)
    allow_symbols = tk.BooleanVar(value=True)
    allow_uppercases = tk.BooleanVar(value=True)
    unsl_pattern = tk.BooleanVar(value=False)

    custom_letters_var = tk.StringVar()
    custom_numbers_var = tk.StringVar()
    custom_symbols_var = tk.StringVar()

    tk.Label(generator_frame, text="Password Length:", font=("Arial", 14), bg="lightgreen").pack(anchor="w")
    tk.Entry(generator_frame, textvariable=length_var).pack(anchor="w")
    tk.Label(generator_frame, text="Quantity:", font=("Arial", 14), bg="lightgreen").pack(anchor="w")
    tk.Entry(generator_frame, textvariable=quantity_var).pack(anchor="w")

    tk.Checkbutton(generator_frame, text="Allow Letters", variable=allow_letters, bg="lightgreen").pack(anchor="w")
    tk.Entry(generator_frame, textvariable=custom_letters_var).pack(anchor="w")

    tk.Checkbutton(generator_frame, text="Allow Numbers", variable=allow_numbers, bg="lightgreen").pack(anchor="w")
    tk.Entry(generator_frame, textvariable=custom_numbers_var).pack(anchor="w")

    tk.Checkbutton(generator_frame, text="Allow Symbols", variable=allow_symbols, bg="lightgreen").pack(anchor="w")
    tk.Entry(generator_frame, textvariable=custom_symbols_var).pack(anchor="w")

    tk.Checkbutton(generator_frame, text="Allow Uppercase", variable=allow_uppercases, bg="lightgreen").pack(anchor="w")
    tk.Checkbutton(generator_frame, text="Use UNSL Pattern", variable=unsl_pattern, bg="lightgreen").pack(anchor="w")

    result_box = tk.Text(generator_frame, height=12, width=70)
    result_box.pack(pady=10)

    def on_generate():
        result_box.delete("1.0", tk.END)
        length = length_var.get()
        unsl_enabled = unsl_pattern.get()
        
        if unsl_enabled:
            if length < 4:
                result_box.insert(tk.END, "ERROR: Password length must be equal or larger than 4 when UNSL pattern is enabled!")
                return
        else:
            if length < 4:
                response = tk.messagebox.askyesno(
                    "Weak Password Warning",
                    f"Password length {length} is very weak and not guaranteed to be secured.\n\nDo you want to proceed?"
                )
                if not response:
                    result_box.insert(tk.END, "Password generation cancelled.")
                    return
        
        try:
            pwds = generate_passwords(
                length=length,
                quantity=quantity_var.get(),
                allow_letters=allow_letters.get(),
                custom_letters=custom_letters_var.get(),
                allow_numbers=allow_numbers.get(),
                custom_numbers=custom_numbers_var.get(),
                allow_symbols=allow_symbols.get(),
                custom_symbols=custom_symbols_var.get(),
                allow_uppercases=allow_uppercases.get(),
                unsl=unsl_enabled
            )
            for pwd, strength in pwds:
                # strength is (label, score, secure)
                label, score, secure = strength
                status = "SECURE" if secure else "NOT SECURE"
                result_box.insert(tk.END, f"{pwd} → {label} (score {score}) [{status}]\n")
        except ValueError as e:
            result_box.insert(tk.END, f"ERROR: {str(e)}")

    tk.Button(generator_frame, text="Generate", font=("Arial", 14, "bold"),
              command=on_generate).pack(pady=10)
    tk.Button(generator_frame, text="<<< Return", font=("Arial", 14),
              command=lambda: switch_menu(generator_frame, main_menu_frame)).pack(pady=10)

    main_menu_frame.pack(fill="both", expand=True)
    root.mainloop()

def switch_menu(hide_frame, show_frame):
    hide_frame.pack_forget()
    show_frame.pack(fill="both", expand=True)

if __name__ == "__main__":
    main()