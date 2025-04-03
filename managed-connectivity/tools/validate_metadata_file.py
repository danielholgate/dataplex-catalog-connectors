import json
import sys
import argparse
from collections import Counter
from jsonschema import validate, ValidationError

## Validate Dataplex Catalog metadata import file

# JSON schema validation
dataplex_entry_schema = """
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "entry": {
      "type": "object",
      "properties": {
        "name": {
          "type": "string",
          "pattern": "^projects/[a-z0-9-]+/locations/[a-z0-9-_]+/entryGroups/[a-z0-9-]+/entries/[a-zA-Z0-9_]+"
        },
        "fully_qualified_name": {
          "type": "string",
          "pattern": "^[a-z]+:`[a-zA-Z0-9_:.-]+`([.][`]*[a-zA-Z0-9_#-$]+[`]*)*$"
        },
        "parent_entry": {
          "type": "string",
          "pattern": "^$|^projects/[a-z0-9-]+/locations/[a-z0-9-_]+/entryGroups/[a-z0-9-]+/entries/[a-zA-Z0-9_]+"
        },
        "entry_source": {
          "type": "object",
          "properties": {
            "display_name": {
              "type": "string"
            },
            "system": {
              "type": "string"
            }
          },
          "required": ["display_name", "system"]
        },
        "aspects": {
          "type": "object",
          "additionalProperties": {
            "type": "object",
            "properties": {
              "aspect_type": {
                "type": "string"
              },
              "data": {
                "type": ["object", "array"],
                "properties":{
                  "fields":{
                    "type":"array",
                    "items":{
                      "type":"object",
                      "properties":{
                        "name":{"type":"string","pattern":"[a-zA-Z]+"},
                        "mode":{"type":"string","pattern":"REQUIRED|NULLABLE"},
                        "dataType":{"type":"string","pattern":"[a-zA-Z]+"},
                        "metadataType":{"type":"string","pattern":"[A-Z]+"}
                      },
                      "required":["name","mode","dataType","metadataType"]
                    }
                  }
                },
                "required": [],
                "if":{
                  "properties":{
                    "aspect_type":{
                      "const":"dataplex-types.global.schema"
                    }
                  }
                },
                "else":{
                  "type":"object"
                }

              },
              "path": {
                "type": "string"
              }
            },
            "required": ["aspect_type", "data"]
          }
        },
        "entry_type": {
          "type": "string",
          "pattern": "^projects/[a-z0-9-_]+/locations/[a-z0-9-_]+/entryTypes/[a-zA-Z0-9_]+"
        }
      },
      "required": ["name", "fully_qualified_name", "entry_type", "aspects"]
    },
    "aspect_keys": {
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "update_mask": {
      "oneOf": [
        {
          "type": "array",
          "items": {
            "type": "string"
          }
        },
        {
          "type": "string"
        }
      ]
    }
  },
  "required": ["entry", "aspect_keys", "update_mask"]
}
"""

def validate_jsonl(file_path : str,isDebug : bool, isList : bool, min_lines: int, exact_lines: int):
    """
    Validates Dataplex Catalog  metadata import file to confirm it is well-formed and values fulfill requirements for import
    """
    is_valid = True

    json_errors_count = 0
    dataplex_entry_error_count = 0
    line_count = 1
    entry_names = []
    entry_types = []
    fqn_list = []
    parents = []
    top_entry_count = 0

    print(f"\nValidating dataplex metadata import file: {file_path}")

    dataplex_schama = json.loads(dataplex_entry_schema)

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if isDebug:
                  print(f"Line {line_count} : ")
                line = line.strip()
                if not line: #skip empty lines
                    print(f"  File has an empty line: {line_count}")
                    continue
                try:
                    #Basic check first to confirm well-formed/valid JSON object
                    obj = json.loads(line)
                    if isDebug:
                       print("  JSON is well-formed")
                    if isList: 
                        print( json.dumps(obj, indent=4) )
                        line_count += 1
                        continue;
                    try:
                        #Validate against schema definition
                        validate(instance=obj, schema=dataplex_schama)
                        if isDebug:
                          print("  JSON conforms to dataplex catalog entry schema")
                    except ValidationError as e:
                        print("  Failed validation against dataplex catalog entry schema:")
                        print(f"  {e}")
                        dataplex_entry_error_count += 1
                        is_valid = False
                        if isDebug:
                            print(json.dumps(obj, indent=4))

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

                    if obj['entry']['aspects'] and 'dataplex-types.global.schema' in obj['entry']['aspects']:
                        data_fields = obj['entry']['aspects']['dataplex-types.global.schema']['data']['fields']
                        for x in data_fields:
                           if x['metadataType'] == 'OTHER':
                              print(f"  FYI: Line {line_count} Entry with {fqn} has column which has been mapped to generic metadata type OTHER")
                              print(f"  {x}")

                except json.JSONDecodeError as e:
                    print(f"Error: Invalid JSON on line {line_count}:\n {line}") 
                    json_errors_count+=1
                except Exception as e:
                    print(f"An unexpected error occured on line {line_count}: {e}")
                    print(f"Offending Line: {line}")
                    is_valid = False
                line_count += 1

        if isList: 
            sys.exit;
        else:
          if json_errors_count > 0:
              print(f"**File has {json_errors_count} malformed lines")
              is_valid = False
          else:
              print("\n==All lines in file are well-formed JSON")

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

                print(f"\nFully Qualified Names:")
                for fqn in set_fqn:
                    print(f"{fqn}")

        # Find any rouge parent names
              parent_error = 0
              for parent in set_parents:
                if len(parent) > 0 and not parent in set_entrynames:
                  print(f"**Found unknown parent {parent}")
                  parent_error += 1
                  is_valid = False;
              if parent_error == 0:
                print("==All parent entries found")
    
        # FINAL SUMMARY
        print(f"==File has {line_count} lines")
        if dataplex_entry_error_count > 0:
           print(f"**File has {dataplex_entry_error_count} invalid entries")
        else:
           print(f"==All entries passsed validation against dataplex entry schema")

        if exact_lines is not False and line_count != exact_lines:
          print(f"**File has different number of lines to exact_lines value {exact_lines}")
          is_valid = False

        if min_lines is not False and line_count < min_lines:
          print(f"**File has less lines than mint_lines value {min_lines}")
          is_valid = False

        if is_valid:
            print("File is VALID")
        else:
            print("File is NOT VALID")

    except FileNotFoundError:
        print(f"Error: File not found: {file_path}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validates Dataplex Catalog metadata import file (jsonl)")
    parser.add_argument("file_path", help="Path to metadata import file")
    parser.add_argument("--debug",default=False,help="prints details of JSON line validation",  action="store_true")
    parser.add_argument("--list",default=False,help="lists out the lines in the file", action="store_true")
    parser.add_argument("--min_lines",type=int,default=False,help="minimum number of lines that must be in file")
    parser.add_argument("--exact_lines",type=int,default=False,help="exact number of lines that must be in file")
    args = parser.parse_args()

    validate_jsonl(args.file_path,args.debug,args.list,args.min_lines, args.exact_lines)