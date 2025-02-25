"""Command line reader."""

import argparse


def read_args():
    """Reads arguments from the command line."""
    parser = argparse.ArgumentParser()

    # Project arguments
    parser.add_argument("--target_project_id", type=str, required=True,
        help="The name of the target Google Cloud project to import the metadata into.")
    parser.add_argument("--target_location_id", type=str, required=True,
        help="The target Google Cloud location where the metadata will be imported into.")
    parser.add_argument("--target_entry_group_id", type=str, required=True,
        help="The ID of the Dataplex Entry Group to import metadata into. "
             "Metadata will be imported into entry group with the following"
             "full resource name: projects/${target_project_id}/"
             "locations/${target_location_id}/entryGroups/${target_entry_group_id}.")

    # Oracle specific arguments
    parser.add_argument("--host", type=str, required=True,
        help="Oracle host server")
    parser.add_argument("--port", type=str, required=True,
        help="The port number (usually 1521)")
    parser.add_argument("--user", type=str, required=True, help="Oracle User")
    parser.add_argument("--password-secret", type=str, required=True,
        help="Resource name in the Google Cloud Secret Manager for the Oracle password")
    #parser.add_argument("--exclude-schemas", type=str,required=False,
    #    help="Additional schemas to be excluded from metadata extract (comma seperated list)")
    # User must provide either an Oracle SID OR a service name to connect
    group = parser.add_argument_group('service_or_sid', 'Oracle Service or SID')
    exclusive_group = group.add_mutually_exclusive_group(required=True)
    exclusive_group.add_argument("--service", type=str, help="Oracle Service name to connect to")
    exclusive_group.add_argument("--sid", type=str, help="Oracle SID (Service Identifier) to connect to. For older Oracle versions")
 
    # Google Cloud Storage arguments
    # It is assumed that the bucket is in the same region as the entry group
    parser.add_argument("--output_bucket", type=str, required=True,
        help="The Cloud Storage bucket to write the generated metadata import file. Format begins with gs:// ")
    parser.add_argument("--output_folder", type=str, required=True,
        help="The folder within the Cloud Storage bucket, to write the generated metadata import files. Name only required")

    # Development arguments
    parser.add_argument("--testing", type=str, required=False,
    help="Test mode")
    
    return vars(parser.parse_known_args()[0])
