"""Command line reader."""

import argparse, sys

def read_args():
    """Reads arguments from the command line."""
    parser = argparse.ArgumentParser()

    # Project arguments
    parser.add_argument("--target_project_id", type=str, required=True,
                        help="Google Cloud project ID metadata entries will be import into")
    parser.add_argument("--target_location_id", type=str, required=True,
                        help="Location of Google Cloud location metadata will be imported into")
    parser.add_argument("--target_entry_group_id", type=str, required=True,
                        help="Dataplex Entry Group ID to import metadata into")

    # Snowflake specific arguments
    parser.add_argument("--account", type=str, required=True,
                        help="Snowflake account to connect to. Format is [account_locator].[region]. For example: xy12345.us-central1")
    parser.add_argument("--user", type=str, required=True, help="Snowflake User")

    credentials_group = parser.add_mutually_exclusive_group()
    credentials_group.add_argument("--password_secret", type=str,help="Google Cloud Secret Manager ID for the password")
    credentials_group.add_argument("--token", type=str, help="Authentication token for oauth")
    
    parser.add_argument("--database", type=str, required=True, help="Snowflake database")
    parser.add_argument("--authenticaton", type=str, required=False,choices=['oauth','password'],help="Authentication method")
    parser.add_argument("--warehouse", type=str,required=False,help="Snowflake warehouse")
    parser.add_argument("--schema", type=str,required=False,help="Snowflake schema")

    # Google Cloud Storage arguments
    parser.add_argument("--output_bucket", type=str, required=True,
                        help="Cloud Storage bucket to write generated metadata import file to. Do not include gs:// prefix ")
    parser.add_argument("--output_folder", type=str, required=False,
                        help="Folder within bucket where generated metadata import file will be written. Name only required")

    # Development arguments
    parser.add_argument("--testing", type=str, required=False,help="Test mode")

    parsed_args = parser.parse_known_args()[0]

    if parsed_args.authenticaton == 'oauth' and parsed_args.token is None:
        print("--token must also be supplied if using oauth authentication")
        sys.exit(1)
    
    return vars(parsed_args)
