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
from google.cloud import dataplex_v1

## Creates required Entry Group, Entry Types, Aspect Types from a metadata import file

def create_entry_group(
    project_id: str, location: str, entry_group_id: str
) -> dataplex_v1.EntryGroup:
    """Method to create Entry Group located in project_id, location and with entry_group_id"""

    with dataplex_v1.CatalogServiceClient() as client:
        # The resource name of the Entry Group location
        parent = f"projects/{project_id}/locations/{location}"
        entry_group = dataplex_v1.EntryGroup(
            description="description of the entry group"
        )
        create_operation = client.create_entry_group(
            parent=parent, entry_group=entry_group, entry_group_id=entry_group_id
        )
        print(f"Created Entry Group: projects/{project_id}/locations/{location}/entryGroups/{entry_group_id}")
        return create_operation.result(60)

def create_entry_type(
    project_id: str, location: str, entry_type_id: str
) -> dataplex_v1.EntryType:
    """Method to create Entry Type located in project_id, location and with entry_type_id"""

    print(f"Creating Entry Type {entry_type_id}")

    typeAliases = []

    if "-table" in entry_type_id:
        typeAliases.append("TABLE")

    if "-view" in entry_type_id:
        typeAliases.append("VIEW")

    if "-database" in entry_type_id:
        typeAliases.append("DATABASE")

    with dataplex_v1.CatalogServiceClient() as client:
        # The resource name of the Entry Type location
        parent = f"projects/{project_id}/locations/{location}"
        entry_type = dataplex_v1.EntryType(
            description="description of the entry type",
            # Required aspects will need to be attached to every entry created for this entry type.
            # You cannot change required aspects for entry type once it is created.

            type_aliases=typeAliases,
            
            required_aspects=[
               # dataplex_v1.EntryType.AspectInfo(
                    # Example of system aspect type.
                    # It is also possible to specify custom aspect type.
               #     type="projects/dataplex-types/locations/global/aspectTypes/generic"
               # )
            ],
        )
        create_operation = client.create_entry_type(
            parent=parent, entry_type=entry_type, entry_type_id=entry_type_id
        )
        return create_operation.result(60)

def create_entry_aspect_types(file_path : str, project : str, location : str):

    entry_types = []
    aspect_types = []
    entry_names = []
    entry_groups = []
    locations = []
    projects = []

    line_count = 0

    try:
        with open(file_path, 'r', encoding='utf-8') as f:

            for line in f:

                line_count += 1

                line = line.strip()
                if not line: #skip empty lines
                    continue
                try:
                    obj = json.loads(line)

                    # collect entry type
                    entry_type = (obj['entry']['entryType'])
                    entry_types.append(entry_type)

                    # collect aspect types
                    if obj['entry']['aspects']:
                        for aspect_type in obj['entry']['aspects']:
                          aspect_types.append(aspect_type)

                    # collect entry names
                    entry_name = obj['entry']['name']
                    entry_names.append(entry_name)

                    try:
                        parent_entry_name = obj['entry']['parentEntry']
                        entry_names.append(parent_entry_name)
                    except:
                        print("Entry has no parentName property. Ignoring")
                    

                except Exception as e:
                    print(f"Line {line_count} An unexpected error occured during property inspection of metadata file: {e}")

    except FileNotFoundError:
        print(f"Error: File not found: {file_path}")
    except Exception as e:
        print(f"Unexpected error occurred: {e}")

    # Deduplicate aspect types and entry types
    set_entrytypes = set(entry_types)

    set_entrytypesonly = []

    etregex = r'entryTypes/([^/]+)'
    for et in set_entrytypes:
        match = re.search(etregex,et)
        if match:
            set_entrytypesonly.append(match.group(1))

    set_aspecttypes = set(aspect_types)
    set_entrynames = set(entry_names)

  # Extract Entry Group(s), Location, Projects from entry names
    egregex = r'entryGroups/([^/]+)'
    locregex = r'locations/([^/]+)'
    projregex = r'projects/([^/]+)'

    for en in set_entrynames:
        match = re.search(egregex,en)
        if match:
            entry_groups.append(match.group(1))

        lmatch = re.search(locregex,en)
        if lmatch:
            locations.append(lmatch.group(1))

        pmatch = re.search(projregex,en)
        if pmatch:
            projects.append(pmatch.group(1))

    set_entrygroups = set(entry_groups)
    set_locations = set(locations)
    set_projects = set(projects)

    if len(set_projects) > 1 or len(set_projects) == 0:
        print("Project error in file: {set_projects}")
        sys.exit()
    if len(set_locations) > 1 or len(set_locations) == 0:
        print("locations error in file: {set_projects}")
        sys.exit()
    if len(set_entrygroups) > 1 or len(set_entrygroups) == 0:
        print("Entry Groups error in file: {set_entrygroups}")
        sys.exit()
    
    if location is None:
        location = set_locations.pop()
    if project is None:
        project = set_projects.pop()
    entrygroup = set_entrygroups.pop()

    print(f"Project: {projects}")
    print(f"Location: {location}")
    print(f"Entry Group: {entrygroup}")

    try:
        create_entry_group(project,location,entrygroup)
    except:
        print(f"Exception occured trying to creare Entry Group {entrygroup} in project: {project} location: {location}")

    for et in set_entrytypesonly:
        try:
            create_entry_type(project,location,et)
        except:
            print(f"Exception occured trying to creare Entry Type {et} in project: {project} location: {location}")

    print(f"Finished")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generates an import request for the Dataplex Import API for a metadata import file (.jsonl)")
    parser.add_argument("file_path", help="Path to metadata import file")
    parser.add_argument("--project",type=str,help="project override", default=None)
    parser.add_argument("--location",type=str,help="location override", default=None)
    args = parser.parse_args()

    create_entry_aspect_types(args.file_path,args.project,args.location)