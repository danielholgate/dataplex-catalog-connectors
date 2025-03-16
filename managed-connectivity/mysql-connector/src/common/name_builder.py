"""Builds Dataplex hierarchy identifiers."""
from typing import Dict
from src.constants import EntryType, SOURCE_TYPE

# Forbidden symbol for Dataplex Entry Names
FORBIDDEN_SYMBOL = "#"
ALLOWED_SYMBOL = "!"

def create_fqn(config: Dict[str, str], entry_type: EntryType,
               schema_name: str = "", table_name: str = ""):
    """Creates a fully qualified name or Dataplex v1 hierarchy name."""
    if FORBIDDEN_SYMBOL in schema_name:
        schema_name = f"`{schema_name}`"

    # INSTANCE
    if entry_type == list(EntryType)[0]:
        # Requires backticks to escape column
        return f"{SOURCE_TYPE}:`{config['host']}`"
    # DATABASE
    if entry_type == list(EntryType)[1]:
        instance = create_fqn(config, list(EntryType)[0])
        return f"{instance}.{config['database']}"
    # TABLE or VIEW
    if entry_type in [list(EntryType)[2], list(EntryType)[3]]:
        database = create_fqn(config, list(EntryType)[0])
        return f"{database}.{schema_name}.{table_name}"
    return ""

def create_name(config: Dict[str, str], entry_type: EntryType,
                schema_name: str = "", table_name: str = ""):
    """Creates a Dataplex v2 hierarchy name."""
    if FORBIDDEN_SYMBOL in schema_name:
        schema_name = schema_name.replace(FORBIDDEN_SYMBOL, ALLOWED_SYMBOL)

    ## EXPERIMENTAL

    # INSTANCE   
    if entry_type == list(EntryType)[0]:
        name_prefix = (
            f"projects/{config['target_project_id']}/"
            f"locations/{config['target_location_id']}/"
            f"entryGroups/{config['target_entry_group_id']}/"
            f"entries/"
        )
        return name_prefix + config["host"].replace(":", "@")
     # DATABASE   
    if entry_type == list(EntryType)[1]:
        instance = create_name(config, list(EntryType)[0])
        return f"{instance}/databases/{config['database']}"
     # TABLE   
    if entry_type == list(EntryType)[2]:
        db_schema = create_name(config, list(EntryType)[1], schema_name)
        return f"{db_schema}/tables/{table_name}"
     # VIEW   
    if entry_type == list(EntryType)[3]:
        db_schema = create_name(config, list(EntryType)[1], schema_name)
        return f"{db_schema}/views/{table_name}"
    return ""


def create_parent_name(config: Dict[str, str], entry_type: EntryType,
                       parent_name: str = ""):
    """Generates a Dataplex v2 name of the parent."""
    # DATABASE
    if entry_type == list(EntryType)[1]:
        return create_name(config, list(EntryType)[0])
    if entry_type == EntryType.TABLE:
        return create_name(config, list(EntryType)[1], parent_name)
    return ""


def create_entry_aspect_name(config: Dict[str, str], entry_type: EntryType):
    """Generates an entry aspect name."""
    last_segment = entry_type.value.split("/")[-1]
    return f"{config['target_project_id']}.{config['target_location_id']}.{last_segment}"
