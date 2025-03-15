"""Command line reader."""

import argparse,sys

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
                        help="Name of the target Google Cloud project to import the metadata into. Generated Entries will use this project")
    parser.add_argument("--target_location_id", type=str, required=True,
                        help="Target Google Cloud location metadata will be imported into. Generated Entries will use this location")
    parser.add_argument("--target_entry_group_id", type=str, required=True,
                        help="The ID of the Dataplex Entry Group to import metadata into")

    # Mysql specific arguments
    parser.add_argument("--host", type=str, required=True,
                        help="Mysql host server")
    parser.add_argument("--port", type=str, required=True,
                        help="The port number (usually 3306)")
    parser.add_argument("--database", type=str, required=True,
                        help="Mysql database to connect to")
    parser.add_argument("--user", type=str, required=True, help="Mysql User")
    parser.add_argument("--password-secret", type=str, required=True,
                        help="Resource name in the Google Cloud Secret Manager for the Mysql password")

    # Google Cloud Storage arguments
    # It is assumed that the bucket is in the same region as the entry group
    parser.add_argument("--output_bucket", type=str, required=True,
                        help="The Cloud Storage bucket to write the generated metadata import file. Do not include gs:// ")
    parser.add_argument("--output_folder", type=str, required=False,action=ValidateGCS,
                        help="The folder within the Cloud Storage bucket, to write the generated metadata import files. Name only required")

    # Development arguments
    parser.add_argument("--testing", type=str, required=False,
    help="Test mode")
    
    return vars(parser.parse_known_args()[0])
