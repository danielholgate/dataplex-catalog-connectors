# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import re
import sys
import argparse
from collections import Counter

## Creates an import request for the Dataplex metadata import API

REQUEST_TEMPLATE = '''
{
"type": "IMPORT",
"import_spec": {
  "source_storage_uri": "gs://your-metadata-file-gcs-bucket/",
  "scope": {
    "entryGroups": [],
    "entry_types": [],
    "aspect_types":[]
    },
  "entry_sync_mode": "FULL",
  "aspect_sync_mode": "INCREMENTAL",
  "log_level": "DEBUG"
  }
}
'''

def generate_import(file_path : str, output_filename : str):

    entry_types = []
    aspect_types = []
    entry_names = []
    entry_groups = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line: #skip empty lines
                    continue
                try:
                    obj = json.loads(line)

                    # collect entry type
                    entry_type = (obj['entry']['entry_type'])
                    entry_types.append(entry_type)

                    # collect aspect types
                    if obj['entry']['aspects']:
                        for aspect_type in obj['entry']['aspects']:
                          aspect_types.append(aspect_type)

                    # collect entry names
                    entry_name = obj['entry']['name']
                    parent_entry_name = obj['entry']['parent_entry']
                    entry_names.append(entry_name)
                    entry_names.append(parent_entry_name)

                except Exception as e:
                    print(f"An unexpected error occured: {e}")

    except FileNotFoundError:
        print(f"Error: File not found: {file_path}")
    except Exception as e:
        print(f"Unexpected error occurred: {e}")

    # Deplicate aspect types and entry types
    set_entrytypes = set(entry_types)
    set_aspecttypes = set(aspect_types)
    set_entrynames = set(entry_names)

  # Extract Entry Group(s) from entry names
    regex = r"^(.*/entryGroups/[^/]+)"
    for en in set_entrynames:
      match = re.search(regex,en)
      if match:
        entry_groups.append(match.group(1))
    set_entrygroups = set(entry_groups)

    entry_template_obj = json.loads(REQUEST_TEMPLATE)
    
    for et in set_entrytypes:
        entry_template_obj['import_spec']['scope']['entry_types'].append(et)
    for at in set_aspecttypes:
        at_split = at.split('.')
        if len(at_split) != 3:
            print(f"Error: AspectType does not have three sections: {at}")
            sys.exit()
        formatted_AspectType = f"projects/{at_split[0]}/locations/{at_split[1]}/aspectTypes/{at_split[2]}"
        entry_template_obj['import_spec']['scope']['aspect_types'].append(formatted_AspectType)
    
    for en in set_entrygroups:
        entry_template_obj['import_spec']['scope']['entryGroups'].append(en)

    print( f"\n{json.dumps(entry_template_obj, indent=4)}" )

    with open(output_filename,"w") as f:
      f.writelines(json.dumps(entry_template_obj, indent=4))

    print(f"\nGenerated import file: {output_filename}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Genenerates an import request for the Dataplex Import API for a metadata import file (.jsonl)")
    parser.add_argument("file_path", help="Path to metadata import file")
    parser.add_argument("--output_filename",help="Name of output file (optional)",default="metadata_import_request.json")
    args = parser.parse_args()

    generate_import(args.file_path,args.output_filename)