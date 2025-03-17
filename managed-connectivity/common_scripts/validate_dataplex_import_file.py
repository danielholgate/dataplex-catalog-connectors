import json
import sys
import argparse
from collections import Counter

## Dataplex Catalog Metadata Import file check

def validate_jsonl(file_path : str,isDebug : bool):
    """
    Examines Dataplex Catalog JSONL metadata import file, iterates through each line, and checks if it's valid.

    Args:
        file_path (str): The path to the JSONL file.
        --debug Y/N : Include details of lines
    """
    is_valid = True

    json_errors_count = 0
    line_count = 1
    entry_names = []
    entry_types = []
    fqn_list = []
    parents = []
    top_entry_count = 0

    print(f"Checking dataplex metadata file: {file_path}")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                print(f"Line {line_count} : ")
                line = line.strip()
                if not line: #skip empty lines
                    print(f"Skipping empty line {line_count}")
                    continue
                try:
                    #Check it's a well formed JSON object
                    obj = json.loads(line)
                    if isDebug:
                        print(json.dumps(obj, indent=4))
                    print("   Valid JSON")

                    # Get the entry and parent entry
                    parent_entry = (obj['entry']['parent_entry'])
                    if len(parent_entry) == 0:
                        top_entry_count+=1
                    parents.append(parent_entry)
                    entry_name = entry_names.append(obj['entry']['name'])
                    entry_names.append(entry_name)
                    entry_type = (obj['entry']['entry_type'])
                    entry_types.append(entry_type)
                    fqn = obj['entry']['fully_qualified_name']
                    fqn_list.append(fqn)

                    # Check table and view aspects
                    if obj['entry']['aspects'] and 'dataplex-types.global.schema' in obj['entry']['aspects']:
                        if 'data' in obj['entry']['aspects']['dataplex-types.global.schema']:
                            if 'fields' in obj['entry']['aspects']['dataplex-types.global.schema']['data']:
                                    print(f"   Checking fields data for {fqn}  ", end='')
                                    for d in (obj['entry']['aspects']['dataplex-types.global.schema']['data']['fields']):
                                        name = d['name']
                                        mode = d['mode']
                                        dt = d['dataType']
                                        mdt = d['metadataType']
                                        if len(mode) == 0 or len(name) == 0 or len(dt) == 0 or len(mdt) == 0:
                                            print("   Required attritbute in entry was empty: {d}")
                                            is_valid = False 
                                    print("OK")
                                                                          
                    
                except json.JSONDecodeError as e:
                    print(f"Error: Invalid JSON on line {line_count}:\n {line}") #Print the offending line for debugging
                    json_errors_count+=1
                except Exception as e:
                    print(f"An unexpected error occured on line {line_count}: {e}")
                    print(f"Offending Line: {line}")
                    is_valid = False
                line_count += 1

        if json_errors_count > 0:
            print(f"File has {json_errors_count} malformed lines")
            is_valid = False
        else:
            print("1. All lines in file are well formed JSON")

        set_fqn = set(fqn_list)
        set_entrynames = set(entry_names)
        set_entrytypes = set(entry_types)
        set_parents = set(parents)

        if isDebug:

            print(f"\nEntity Names:")
            for entry in set_entrynames:
                print(f"{entry}")
        
            print(f"\nEntity Types:")
            for entry in set_entrytypes:
                print(f"{entry}")

            print(f"\nFQN:")
            for fqn in set_fqn:
                print(f"{fqn}")

        # Find any rouge parent names
        parent_error = 0
        for parent in set_parents:
            if len(parent) > 0 and not parent in set_entrynames:
                print(f"Invalid File: Found unknown parent {parent}")
                parent_error += 1
        if parent_error == 0:
                print("2. All parent entries found")

        # FINAL SUMMARY
        if is_valid:
            print("File is VALID")
        else:
            print("File is NOT VALID")


    except FileNotFoundError:
        print(f"Error: File not found: {file_path}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate JSONL file.")
    parser.add_argument("file_path", help="Path to the JSONL file.")
    parser.add_argument("--debug",help="if present then prints details of JSON lines")
    args = parser.parse_args()

    validate_jsonl(args.file_path,(args.debug == 'Y'))