def generate_next_id(last_id):
    # Split the latest ID into prefix and sequential part
    prefix, sequential_part = last_id.split("-")

    # Extract the letter and numeric parts
    letter_part = sequential_part[:-4]
    numeric_part = sequential_part[-4:]

    # Increment the numeric part

    new_numeric_part = str(int(numeric_part) + 1).zfill(4)

    # Check if numeric part reaches '999' and increment the letter part
    if new_numeric_part == "10000":
        letter_part = increment_letter_part(letter_part)
        new_numeric_part = "0001"

    # Generate the next ID
    next_id = f"{prefix}-{letter_part}{new_numeric_part}"
    return next_id


def increment_letter_part(letter_part):
    # Example: AAA -> AAB, ZZZ -> AAA
    for i in range(len(letter_part) - 1, -1, -1):
        if letter_part[i] != "Z":
            letter_part = (
                letter_part[:i]
                + chr(ord(letter_part[i]) + 1)
                + "A" * (len(letter_part) - i - 1)
            )
            return letter_part
    return "A" + "A" * len(letter_part)
