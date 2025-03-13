import json
import sys
import argparse
from collections import Counter

def validate_jsonl(file_path):
    """
    Opens a JSONL file, iterates through each line, and checks if it's valid JSON.

    Args:
        file_path (str): The path to the JSONL file.
    """
    json_errors_count = 0
    line_count = 1
    entry_names = []
    entry_types = []
    parents = []
    top_entry_count = 0

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line: #skip empty lines
                    print(f"Skipping empty line {line_count}")
                    continue
                try:
                    #Check it's a well formed JSON object
                    obj = json.loads(line)
                    parent_entry = (obj['entry']['parent_entry'])
                    if len(parent_entry) == 0:
                        top_entry_count+=1
                    parents.append(parent_entry)
                    entry_name = entry_names.append(obj['entry']['name'])
                    entry_names.append(entry_name)
                    entry_type = (obj['entry']['entry_type'])
                    entry_types.append(entry_type)
                    
                except json.JSONDecodeError as e:
                    print(f"Error: Invalid JSON on line {line_count}:\n Line is {line}") #Print the offending line for debugging
                    json_errors_count+=1
                except Exception as e:
                    print(f"An unexpected error occured on line {line_count}: {e}")
                    print(f"Offending Line: {line}")
                line_count += 1
        print(f"File has:")
        print(f"{line_count} lines. {json_errors_count} lines with json errors")

        set_entrynames = set(entry_names)
        set_parents = set(parents)

        for entry in set_entrynames:
            print(f"EntryName: {entry}")

        # Find any rouge parent names
        for parent in set_parents:
            if len(parent) > 0 and not parent in set_entrynames:
                print(f"Invalid File: Found unknown parent {parent}")


        #if set_entrynames.issubset(set_parents):
        #    print("EntryNames is subset of parents")
        
        #if set_entrynames.issuperset(set_parents):
        #    print("EntryNames is superset of parents")

        #print(set_entrynames)

        entrytype_counts = dict(Counter(entry_types))
        entryname_counts = dict(Counter(entry_names))

        #if top_entry_count > 1:
        #    print(f"Import file has more than one top entry. Instead has {top_entry_count}")
        #else:
        #    if top_entry_count == 0:
        #        print("Import file no top entry")

    except FileNotFoundError:
        print(f"Error: File not found: {file_path}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate JSONL file.")
    parser.add_argument("file_path", help="Path to the JSONL file.")
    args = parser.parse_args()

    validate_jsonl(args.file_path)