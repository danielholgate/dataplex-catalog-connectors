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
from typing import List
from google.cloud import dataplex_v1

## Creates required Entry Group, Entry Types, Aspect Types from a metadata import file

def create_entry_group(
    project_id: str, location: str, entry_group_id: str
) -> dataplex_v1.EntryGroup:
    """Create Entry Group identified by entry_group_id, located in project_id, locatio """

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
    """Create Entry Type identified by entry_type_id, located in project_id, location """

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
    
def create_aspect_type(
    project_id: str, location: str, aspect_type_id: str,
) -> dataplex_v1.AspectType:
    """Create Aspect Type identified by aspect_type_id, located in project_id, location """

    aspect_fields = List[dataplex_v1.AspectType.MetadataTemplate]

    with dataplex_v1.CatalogServiceClient() as client:
        # The resource name of the Aspect Type location
        parent = f"projects/{project_id}/locations/{location}"

        # Define the Aspect Type resource.
        # It requires a metadata_template (a JSON schema) to define the
        # properties of the Aspect.

        aspect_field = dataplex_v1.AspectType.MetadataTemplate(
        # The name must follow regex ^(([a-zA-Z]{1})([\\w\\-_]{0,62}))$
        # That means name must only contain alphanumeric character or dashes or underscores,
        # start with an alphabet, and must be less than 63 characters.
        name="name_of_the_field",
        # Metadata Template is recursive structure,
        # primitive types such as "string" or "integer" indicate leaf node,
        # complex types such as "record" or "array" would require nested Metadata Template
        type="string",
        index=1,
        annotations=dataplex_v1.AspectType.MetadataTemplate.Annotations(
            description="description of the field"
        ),
        constraints=dataplex_v1.AspectType.MetadataTemplate.Constraints(
            # Specifies if field will be required in Aspect Type.
            required=False
        ),
        )
        
        aspect_fields = [aspect_field]

        aspect_type = dataplex_v1.AspectType(
            description="description of the aspect type",
            metadata_template=dataplex_v1.AspectType.MetadataTemplate(
                # The name must follow regex ^(([a-zA-Z]{1})([\\w\\-_]{0,62}))$
                # That means name must only contain alphanumeric character or dashes or underscores,
                # start with an alphabet, and must be less than 63 characters.
                name="name_of_the_template",
                type="record",
                # Aspect Type fields, that themselves are Metadata Templates.
                record_fields=aspect_fields,
            ),
        )

        create_operation = client.create_aspect_type(
            parent=parent,
            aspect_type=aspect_type,
            aspect_type_id=aspect_type_id
        )

        # Dataplex operations are long-running, so we wait for the result.
        # The timeout is set to 120 seconds (2 minutes).
        print("Waiting for creation operation to complete...")
        try:
            response = create_operation.result(timeout=30)
        except Exception as e:
            print(f"Error during Aspect Type creation: {e}")
            raise

        print(
            f"Successfully created Aspect Type: projects/{project_id}/locations/{location}/aspectTypes/{aspect_type_id}"
        )
        return response

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
    set_aspecttypes = set(aspect_types)

    set_entrytypesonly = []

    etregex = r'entryTypes/([^/]+)'
    for et in set_entrytypes:
        match = re.search(etregex,et)
        if match:
            set_entrytypesonly.append(match.group(1))

    set_aspecttypesonly = []

    atregex = r'aspectType/([^/]+)'
    for at in set_aspecttypes:
        if at == 'dataplex-types.global.schema':
            continue
        set_aspecttypesonly.append(at)

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

    # Build sets of unique entry groups, locations, projects 
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
    
    # If user-provided value for project or location on command line, use that instead of values from file
    if project is None:
        project = set_projects.pop()
        print(f"Will create in project {project} from metadata file")
    else:
        print(f"Will create in project in project {project}")
    if location is None:
        location = set_locations.pop()
        print(f"Will create in location {location} from metadata file")
    else:
        print(f"Will create in location {location}")

    print("\n")

    entrygroup = set_entrygroups.pop()

    try:
        create_entry_group(project,location,entrygroup)
    except Exception as e:
        print(f"Error occured trying to create Entry Group '{entrygroup}' in project {project}, location {location}:\n{e}")

    for et in set_entrytypesonly:
        try:
            create_entry_type(project,location,et)
        except Exception as e:
            print(f"Error occured trying to create Entry Type '{et}' in project {project}, location {location}:\n{e}")
    
    for at in set_aspecttypesonly:
        aspectID = at.split(".")[2]
        print(f"Creating Aspect Type {aspectID}")
        try:
            create_aspect_type(project,location,aspectID)
        except Exception as e:
            print(f"Error occured trying to create Aspect Type '{aspectID}' in project {project}, location {location}:\n{e}")

    print(f"Finished")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Creates Entry Group, Entry Types, Aspect Types from a dataplex catalog metadata import file (.jsonl)")
    parser.add_argument("file_path", help="Path to metadata import file")
    parser.add_argument("--project",type=str,help="Optional project override for creating hierarchy in another project", default=None)
    parser.add_argument("--location",type=str,help="Optional location override for creating hierarchy in another location", default=None)
    args = parser.parse_args()

    print(f"\nCreating Dataplex Universal Catalog Entry Group, Entry Types, Aspect Types from metadata import file:\n {args.file_path}")

    create_entry_aspect_types(args.file_path,args.project,args.location)