import json
import inspect

def print_json_nicely(json_string: str):
    """
    Parses a JSON string and prints it in a nicely formatted way,
    including the caller's file and line number.

    Args:
        json_string: The JSON string to format and print.
    """
    # Get the frame of the caller
    frame = inspect.currentframe().f_back
    filename = inspect.getfile(frame)
    lineno = frame.f_lineno

    print(f"--- Called from: {filename}:{lineno} ---")
    try:
        parsed_json = json.loads(json_string)
        formatted_json = json.dumps(parsed_json, indent=4, sort_keys=True)
        print(formatted_json)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    print("--- End JSON ---")


# Example usage:
# if __name__ == "__main__":
#     ugly_json = '{"name": "John Doe", "age": 30, "isStudent": false, "courses": [{"title": "History", "credits": 3}, {"title": "Math", "credits": 4}], "address": {"street": "123 Main St", "city": "Anytown"}}'
#     print_json_nicely(ugly_json)
#
#     invalid_json = '{"name": "John Doe", "age": 30,' # Missing closing brace
#     print_json_nicely(invalid_json)