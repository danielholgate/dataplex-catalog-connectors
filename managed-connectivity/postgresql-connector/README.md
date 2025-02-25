# PostgreSQL Connector

This custom connector exports metadata for tables and views from PostgreSQL databases to create a [metadata import file](https://cloud.google.com/dataplex/docs/import-metadata#components) for Google Cloud Dataplex. 
You can read more about custom connectors in the documentation for [Dataplex Managed Connectivity framework](https://cloud.google.com/dataplex/docs/managed-connectivity-overview) and [Developing a custom connector](https://cloud.google.com/dataplex/docs/develop-custom-connector) for Dataplex.

## Prepare your PostgreSQL environment:

1. Create a user in the PostgreSQL instance(s) which will be used by Dataplex to connect and extract metadata about tables and views. This user requires the following PostgreSQL privileges and roles: 
    * CONNECT and CREATE SESSION
    * SELECT on information_schema.tables
    * SELECT on information_schema.columns
    * SELECT on information_schema.views
2. Add the password for the user to the Google Cloud Secret Manager in your project and note the Secret ID (format is: projects/[project-number]/secrets/[secret-name])

### Parameters
The PostgreSQL connector takes the following parameters:
|Parameter|Description|Required/Optional|
|---------|------------|-------------|
|target_project_id|GCP Project ID/Project Number, or 'global'. Used in the generated Dataplex Entry, Aspects and AspectTypes|REQUIRED|
|target_location_id|GCP Region ID, or 'global'. Used in the generated Dataplex Entry, Aspects and Aspect Types|REQUIRED|
|target_entry_group_id|Dataplex Entry Group ID to use in the generated entries|REQUIRED|
|host|PostgreSQL server to connect to|REQUIRED|
|port|PostgreSQL server port (usually 5432)|REQUIRED|
|database|PostgreSQL database to connect to|REQUIRED
|user|PostgreSQL username to connect with|REQUIRED|
|password-secret|GCP Secret Manager ID holding the password for the PostgreSQL user. Format: projects/[PROJ]/secrets/[SECRET]|REQUIRED|
|output_bucket|GCS bucket where generated metadata file will be stored. Without gs:// prefix|REQUIRED|
|output_folder|Folder in the GCS bucket where output file will be stored|REQUIRED|

## Extract metadata by running the connector from the command line:

You can run the connector directly from the command line for testing or development purposes.

### Required IAM Roles
- roles/secretmanager.secretAccessor
- roles/storage.objectUser

Be sure to your session is authenticated as a user which has these roles at minimum (ie using ```gcloud auth application-default login```)

### Prepare the environment:
1. Download **postgresql-42.7.5.jar** [from PostgreSQL.org](https://jdbc.postgresql.org/download/)
2. Edit the SPARK_JAR_PATH variable in [postgres_connector.py](src/postgres_connector.py) to match the location of the jar file
3. Ensure a Java Runtime Environment (JRE) is installed in your environment
4. Install PySpark: `pip3 install pyspark`
5. Install all dependencies from the requirements.txt file with `pip3 install -r requirements.txt`

### Running the metadata extraction
To execute a metadata extraction run the following command (substituting appropriate values for your environment):

```shell 
python3 main.py \
--target_project_id my-gcp-project-id \
--target_location_id us-central1 \
--target_entry_group_id postgresql \
--host the-postgres-server \
--port 5432 \
--user dataplexagent \
--password-secret projects/73813454526/secrets/dataplexagent_postgres \
--database my_database \
--output_bucket dataplex_connectivity_imports \
--output_folder postgresql
```

### Output:
The connector generates a metadata extract in JSONL format as described [in the documentation](https://cloud.google.com/dataplex/docs/import-metadata#metadata-import-file). A sample output from the connector can be found [here](sample/postgres-output-dvdrental.jsonl)

## Build a container and extract metadata using Dataproc Serverless

To build a Docker container for the connector and run the extraction process as a [Dataproc Serverless](https://cloud.google.com/dataproc-serverless/docs) job:

### Building the container
1. Run the script ```build_and_push_docker.sh``` to build the Docker container and store it in Artifact Registry. This process can take take up to 10 minutes.
2. Create a GCS bucket which will be used for Dataproc Serverless as a working directory (add to the **--deps-bucket** parameter below)

### Submitting a metadata extraction job to Dataproc serverless:
Once the container is built you can run the metadata extract with the following command (substituting appropriate values for your environment). 

The service account you submit for the job needs the following roles:

- roles/dataplex.catalogEditor
- roles/dataplex.entryGroupOwner
- roles/dataplex.metadataJobOwner
- roles/dataproc.admin
- roles/dataproc.editor
- roles/dataproc.worker
- roles/iam.serviceAccountUser
- roles/logging.logWriter
- roles/secretmanager.secretAccessor
- roles/workflows.invoker


```shell
gcloud dataproc batches submit pyspark \
    --project=my-gcp-project-id \
    --region=us-central1 \
    --batch=0001 \
    --deps-bucket=dataplex-metadata-collection-usc1 \  
    --container-image=us-central1-docker.pkg.dev/my-gcp-project-id/docker-repo/postgres-pyspark@sha256:dab02ca02f60a9e12767996191b06d859b947d89490d636a34fc734d4a0b6d08 \
    --service-account=440165342669-compute@developer.gserviceaccount.com \
    --network=[Your-Network-Name] \
    main.py \
--  --target_project_id my-gcp-project-id \
    --target_location_id us-central1 \
    --target_entry_group_id postgresql \
    --host the-postgres-server \
    --port 5432 \
    --user dataplexagent \
    --password-secret projects/73813454526/secrets/dataplexagent_postgres \
    --database my_database \
    --output_bucket dataplex_connectivity_imports \
    --output_folder postgresql
```

## Manually importing a metadata import file into Google Dataplex

To import a metadata import file into Dataplex call the Import API with the following:

```http
POST https://dataplex.googleapis.com/v1/projects/PROJECT_NUMBER/locations/LOCATION_ID/metadataJobs?metadataJobId=METADATA_JOB_ID
```

See the [Dataplex documetation](https://cloud.google.com/dataplex/docs/import-metadata#import-metadata) for full instructions about importing metadata.

## Run an end-to-end meatdata extraction and import process from PostgreSQL into Dataplex

To run an end-to-end metadata extraction and import process, run the container via Google Workflows. 

Follow the Dataplex documentation here: [Import metadata from a custom source using Workflows ](https://cloud.google.com/dataplex/docs/import-using-workflows-custom-source)
