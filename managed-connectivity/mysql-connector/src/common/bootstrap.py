"""The entrypoint of a pipeline."""
from typing import Dict
import sys,os
from datetime import datetime
from src.constants import EntryType
from src.constants import SOURCE_TYPE, CONNECTOR_MODULE, CONNECTOR_CLASS
from src.constants import DB_OBJECTS_TO_PROCESS, TOP_ENTRIES
from src.constants import getOutputFileName
from src.common.cmd_reader import loadReferencedFile
from src.common import secret_manager
from src import entry_builder
from src.common import gcs_uploader
from src.common import top_entry_builder
from src.common import ExternalSourceConnector
import importlib


def write_jsonl(output_file, json_strings):
    """Writes entries to file in JSONL format."""
    for string in json_strings:
        output_file.write(string + "\n")

def createOutputFolderName(config: Dict[str, str]):
    currentDate = datetime.now()
    folder = ''
    if config['output_folder'] and len(config['output_folder']) > 0:
        folder = f"{config['output_folder']}/"
    return f"{folder}{currentDate.year}{'{:02d}'.format(currentDate.month)}{'{:02d}'.format(currentDate.day)}-{'{:02d}'.format(currentDate.hour)}{'{:02d}'.format(currentDate.minute)}{'{:02d}'.format(currentDate.second)}"

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

    FOLDERNAME = createOutputFolderName(config)

# Local model writes output to local directory only, otherwise write also to GCS bucket
    if config["local_mode"] is None:
        if config['output_bucket'] is None:
            print("output_bucket must be defined unless running in local_mode")
            sys.exit(1)
        elif not gcs_uploader.checkDestination(config['output_bucket']):
            print(f"Exiting")
            sys.exit(1)
        print(f"GCS output path is {config['output_bucket']}/{FOLDERNAME}")    
    else:
        print("Metadata file will be generated in local 'output' directory")

    # Load data from files if required
    if config['ssl_ca'] is not None:
        config['ssl_ca'] = loadReferencedFile(config['ssl_ca'])
    if config['ssl_cert'] is not None:
        config['ssl_cert'] = loadReferencedFile(config['ssl_cert'])
    if config['ssl_key'] is not None:
        config['ssl_key'] = loadReferencedFile(config['ssl_key'])

    config["password"] = secret_manager.get_password(config["password_secret"])

    # Instantiate connector class 
    ConnectorClass = getattr(importlib.import_module(CONNECTOR_MODULE), CONNECTOR_CLASS)
    connector = ConnectorClass(config)

    # Build output file name
    FILENAME = getOutputFileName(config)
    
    output_path = './output'
    if not os.path.exists(output_path):
        os.mkdir(output_path)

    # Statistics tracking
    entries_count = 0

    with open(f"{output_path}/{FILENAME}", "w", encoding="utf-8") as file:
        # Write top entries that don't require connection to the database
        for entry_enum_index in range(TOP_ENTRIES):    
            file.writelines(top_entry_builder.create(config, list(EntryType)[entry_enum_index]))
            file.writelines("\n")

        # Get schemas, write them and collect into the list
        df_raw_schemas = connector.get_db_schemas()
        schemas = [schema.SCHEMA_NAME for schema in df_raw_schemas.select("SCHEMA_NAME").collect()]
        schemas_json = entry_builder.build_schemas(config, df_raw_schemas).toJSON().collect()

        write_jsonl(file, schemas_json)

        # Ingest database objects for every schema in a list
        for schema in schemas:
            for object_type in DB_OBJECTS_TO_PROCESS:
                print(f"Processing {object_type.name}S for {schema}:  ",end='')
                objects_json = process_dataset(connector, config, schema, object_type)
                print(f"{len(objects_json)}")
                entries_count += len(objects_json)
                write_jsonl(file, objects_json)

    print(f"{entries_count} rows written to file {FILENAME}")
    if not config["local_mode"]: 
        gcs_uploader.upload(config,output_path,FILENAME,FOLDERNAME)