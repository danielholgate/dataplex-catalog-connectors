# Tools

This directory contains tools which can be used for working with metadata import files

### Metadata Validation Tool

[validate_metadata_file.py](validate_metadata_file.py)

Validates dataplex metadata import files (.jsonl). Each line in the file is checked to confirm it is a well-formed JSON object and is validated against the [dataplex entry schema](https://cloud.google.com/dataplex/docs/import-metadata#import-item). Some additional logic checks are also performed.

Setup:
```
 pip3 install -r requirements.txt 
```

To run:
```
 python validate_metadata_file.py file_path_to_metadata_file [ADDITIONAL OPTIONS see below]
```

Options:
 
 * --debug. Prints additional detail about file validation
 * --list. Lists out all JSON object lines in the file with pretty print for readability
 * --min_lines INTEGER. Minimum number of lines that must be in file
 * --exact_lines INTEGER. Exact number of lines that must be in file

