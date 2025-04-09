from src.common.gcs_uploader import checkDestination
from src.common.secret_manager import get_password
import sys

# Standard validation checks and value replacements. Additional checks can be applied in cmd_reader for specific data sources
def validateArguments(parsed_args):

    if parsed_args.local_output_only == False and (parsed_args.output_bucket is None or parsed_args.output_folder is None):
        print("both --output_bucket and --output_folder must be supplied if not using --local_output_only")
        sys.exit(1)

    if not parsed_args.local_output_only and not checkDestination(parsed_args.output_bucket):
            print("Exiting")
            sys.exit(1)     

    if parsed_args.password_secret is not None:
        try:
            parsed_args.password = get_password(parsed_args.password_secret)
        except Exception as ex:
            print(ex)
            print("Exiting")
            sys.exit(1)

    return parsed_args
            