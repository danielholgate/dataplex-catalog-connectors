# Tools
This directory contains tools which can be used for working with metadata import files:

* Metadata Validation tool
* Metadata Import API request generator tool
* Too to Create required aspect types, entry types, entrgy group from an existing metadata import file

Set up:
```bash
pip install -r requirements.txt
```

### Metadata Validation tool
[validate_metadata_file.py](validate_metadata_file.py)

Validates dataplex metadata import files (.jsonl). Each line in the file is checked to confirm it is a well-formed JSON object and validated against the [dataplex entry schema](https://cloud.google.com/dataplex/docs/import-metadata#import-item). Some additional logic checks are also performed.

To run:
```bash
 python validate_metadata_file.py path_to_metadata_file [ADDITIONAL OPTIONS see below]
```

Options:
|Parameter|Value|Description|
|---------|-----|-----------|
|--debug||Prints additional detail about file validation|
|--list||Lists out all JSON object lines in the file with pretty print for readability|
|--min_lines|INTEGER|Minimum number of lines that must be in file to be considered valid|
|--exact_lines|INTEGER|Exact number of lines that must be in file to be considered valid|

### Metadata Import API request generator tool
[generate_metadata_import_request.py](generate_metadata_import_request.py)

Convenience tool to generate a [Metadata Import REST API request](https://cloud.google.com/dataplex/docs/import-metadata#import-metadata) (.json) from an existing metadata import file. Adds the required entry types, aspect types, and entry groups. 

See [here](../oracle-connector/sample/metadata_import_request.json) for an example output. 

To run:
```bash
 python generate_metadata_import_request.py file_path_to_metadata_file [ADDITIONAL OPTIONS see below]
```
Options:
|Parameter|Value|Description|
|---------|-----|-----------|
|--output_filename|name of file|Output file. Default is 'metadata_import_request.json'|
