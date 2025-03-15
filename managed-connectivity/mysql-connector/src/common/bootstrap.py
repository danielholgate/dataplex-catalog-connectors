"""The entrypoint of a pipeline."""
from typing import Dict
import sys,os
from datetime import datetime
from src.constants import EntryType
from src.constants import SOURCE_TYPE
from src.constants import CONNECTOR_MODULE, CONNECTOR_CLASS 
from src.common import secret_manager
from src.common import entry_builder
from src.common import gcs_uploader
from src.common import top_entry_builder
from src.common import ExternalSourceConnector
import importlib

def write_jsonl(output_file, json_strings):
    """Writes a list of string to the file in JSONL format."""

    # For simplicity, dataset is written into the one file. But it is not
    # mandatory, and the order doesn't matter for Import API.
    # The PySpark itself could dump entries into many smaller JSONL files.
    # Due to performance, it's recommended to dump to many smaller files.
    for string in json_strings:
        output_file.write(string + "\n")


def process_dataset(
    connector: ExternalSourceConnector,
    config: Dict[str, str],
    schema_name: str,
    entry_type: EntryType,
):
    """Builds dataset and converts it to jsonl."""
    df_raw = connector.get_dataset(schema_name, entry_type)
    df = entry_builder.build_dataset(config, df_raw, schema_name, entry_type)
    return df.toJSON().collect()

def run(connectorconfig):
    """Runs a pipeline."""
    config = connectorconfig

    if not gcs_uploader.checkDestination(config['output_bucket']):
        print("Exiting")
        sys.exit(1)

    """Build the output folder name and filename"""
    currentDate = datetime.now()
    folder = ''
    if config['output_folder'] and len(config['output_folder']):
        folder = f"{config['output_folder']}/"
    FOLDERNAME = f"{folder}{currentDate.year}{'{:02d}'.format(currentDate.month)}{'{:02d}'.format(currentDate.day)}-{'{:02d}'.format(currentDate.hour)}{'{:02d}'.format(currentDate.minute)}{'{:02d}'.format(currentDate.second)}"
    """Build the default output filename"""
    FILENAME = f"{SOURCE_TYPE}-output.jsonl"

    print(f"GCS output path is {config['output_bucket']}/{FOLDERNAME}")

    try:
        config["password"] = secret_manager.get_password(config["password_secret"])
    except Exception as ex:
        print(ex)
        print("Exiting")
        sys.exit(1)

    # Instantiate specific connector class 
    MyClass = getattr(importlib.import_module(CONNECTOR_MODULE), CONNECTOR_CLASS)
    connector = MyClass(config)

    schemas_count = 0
    entries_count = 0

    # Build the output file name from connection details
    FILENAME = f"{SOURCE_TYPE}-output-{config['database']}.jsonl"
    output_path = './output'

    # check whether directory already exists
    if not os.path.exists(output_path):
        os.mkdir(output_path)

    with open(f"{output_path}/{FILENAME}", "w", encoding="utf-8") as file:
        # Write top entries that don't require connection to the database
        file.writelines(top_entry_builder.create(config, EntryType.INSTANCE))
        file.writelines("\n")
        file.writelines(top_entry_builder.create(config, EntryType.DATABASE))

        # Get schemas, write them and collect to the list
        df_raw_schemas = connector.get_db_schemas()
        schemas = [schema.SCHEMA_NAME for schema in df_raw_schemas.select("SCHEMA_NAME").collect()]
        schemas_json = entry_builder.build_schemas(config, df_raw_schemas).toJSON().collect()

        write_jsonl(file, schemas_json)

        # Ingest tables and views for every schema in a list
        for schema in schemas:
            print(f"Processing tables for {schema}:  ",end='')
            tables_json = process_dataset(connector, config, schema, EntryType.TABLE)
            print(f"{len(tables_json)} tables")
            entries_count += len(tables_json)
            write_jsonl(file, tables_json)
            print(f"Processing views for {schema}: ",end='')
            views_json = process_dataset(connector, config, schema, EntryType.VIEW)
            print(f"{len(views_json)} views")
            entries_count += len(views_json)
            write_jsonl(file, views_json)

    print(f"{schemas_count + entries_count} rows written to file {FILENAME}") 
    gcs_uploader.upload(config,output_path,FILENAME,FOLDERNAME)
