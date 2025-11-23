import random

letters = 'abcdefghijklmnopqrstuvwxyz'
numbers = '1234567890'
symbols = '!@#$%^&*()-=_+'

length = int(input("Enter password length (min 4): "))
if length < 4:
    print("Password length must be at least 4. Defaulting to 8.")
    length = 8

quantity = int(input("Enter number of passwords to generate: "))

letters_input = input("Allow letters? (true/false or custom letters): ").strip()
allow_letters = False
allowed_letters = ""
if letters_input.lower() == "true":
    allow_letters = True
    allowed_letters = letters
elif letters_input.lower() == "false":
    pass
else:
    allowed_letters = letters_input

numbers_input = input("Allow numbers? (true/false or custom numbers): ").strip()
allow_numbers = False
allowed_numbers = ""
if numbers_input.lower() == "true":
    allow_numbers = True
    allowed_numbers = numbers
elif numbers_input.lower() == "false":
    pass
else:
    allowed_numbers = numbers_input

symbols_input = input("Allow symbols? (true/false or custom symbols): ").strip()
allow_symbols = False
allowed_symbols = ""
if symbols_input.lower() == "true":
    allow_symbols = True
    allowed_symbols = symbols
elif symbols_input.lower() == "false":
    pass
else:
    allowed_symbols = symbols_input

allow_uppercases = input("Allow uppercase letters? (true/false): ").lower() == "true"

unsl = input("Use UNSL pattern (Uppercase-Number-Symbol-Lowercase)? (true/false): ").lower() == "true"

allowed_keywords = ""
allowed_keywords += allowed_letters
allowed_keywords += allowed_numbers
allowed_keywords += allowed_symbols
if allow_uppercases:
    allowed_keywords += letters.upper()

passwords = []

def char_type(ch):
    if ch.islower() or ch.isupper():
        return 'letter'
    elif ch.isdigit():
        return 'number'
    else:
        return 'symbol'

def check_strength(password):
    score = 0
    if any(c.isupper() for c in password):
        score += 1
    if any(c.islower() for c in password):
        score += 1
    if any(c.isdigit() for c in password):
        score += 3
    if any(c in symbols for c in password):
        score += 2
    if len(password) >= 8:
        score += 1
    return ("Strong", score) if score >= 8 else ("Weak", score)

for j in range(quantity):
    password = ''
    used_types = set()

    if unsl:
        password += random.choice(letters.upper())
        used_types.add('letter')
        password += random.choice(numbers)
        used_types.add('number')
        password += random.choice(symbols)
        used_types.add('symbol')
        password += random.choice(letters)
        used_types.add('letter')

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

    if not {'letter','number','symbol'}.issubset(used_types):
        continue

    passwords.append(password)
    print(password, "→", check_strength(password))