import argparse,sys
from typing import List
from src.constants import CONNECTOR_SPECIFIC_ARGS

# Validate GCS folder name
class ValidateGCS(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        #if not re.match(r'^[A-Za-z0-9_-]+$', values):
        if values in ['.','..']:
            print(f"Invalid GCS output_folder: {values}")
            print(f"Exiting")
            sys.exit(1)
        setattr(namespace, self.dest, values)

def read_args():
    """Reads arguments from the command line."""
    parser = argparse.ArgumentParser()

    # Project arguments
    parser.add_argument("--target_project_id", type=str, required=True,
                        help="Google Cloud project ID where metadata will be imported. All entries in metadatafile will use this")
    parser.add_argument("--target_location_id", type=str, required=True,
                        help="Google Cloud region where metadata will be imported. All entries in metadatafile will use this")
    parser.add_argument("--target_entry_group_id", type=str, required=True,
                        help="Dataplex Entry Group ID where metadata will be imported")
    parser.add_argument("--local_mode",required=False,default=False,action="store_true",
                        help="Generate metadata file locally, do not push to GCS bucket")
    parser.add_argument("--password_secret", type=str, required=True,
                        help="Secrets Manager ID of the password")

    # Google Cloud Storage bucket arguments
    parser.add_argument("--output_bucket", type=str, required=True,
                        help="Cloud Storage bucket where metadata file will be stored. Do not include gs:// ")
    parser.add_argument("--output_folder", type=str, required=False,action=ValidateGCS,
                        help="The folder within the Cloud Storage bucket, to write the generated metadata import files. Name only required")

    # Add source system specific arguments
    for arg in CONNECTOR_SPECIFIC_ARGS:
        #print(f"Adding args {arg[0]} {arg[1]} {arg[2]} {arg[3]}")
        parser.add_argument(arg[0],type=arg[1],required=arg[2],help=arg[3])
    
    return vars(parser.parse_known_args()[0])
