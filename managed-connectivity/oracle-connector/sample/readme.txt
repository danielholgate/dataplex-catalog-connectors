To use this metadata import file

In oracle_output_sample.jsonl: 
    1. Search and replace all instances of "the-gcp-project" with your project ID
    2. [OPTIONAL] Search and replace all instances of "us-central1" with your region or with "global" 
    3. Upload the .jsonl metadata import file to a Google Cloud Storage bucket

In metadata_import_request.json:
    1. Replace the value in source_storage_uri with the path to your GCS bucket (Note: without the file and ending with /)
    2. Replace "the-gcp-project" with your project ID
    3. Go to the Dataplex UI and ensure the Entry Group as well as Entry Types and Aspect Types seen in metadata_import_reques exist in your project

Import via REST API with:

curl -X POST -H "Authorization: Bearer $(gcloud auth print-access-token)" \
-H "Content-Type: application/json; charset=utf-8" \
-d @metadata_import_request.json \
"https://dataplex.googleapis.com/v1/projects/the-project-id/locations/us-central1/metadataJobs?metadataJobId=a001"