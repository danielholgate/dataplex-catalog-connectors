# Oracle Connector

This custom connector exports metadata for tables and views from Oracle databases to create a [metadata import file](https://cloud.google.com/dataplex/docs/import-metadata#components) which can be imported into Google Dataplex. 
You can read more about custom connectors in the documentation for [Dataplex Managed Connectivity framework](https://cloud.google.com/dataplex/docs/managed-connectivity-overview) and [Developing a custom connector](https://cloud.google.com/dataplex/docs/develop-custom-connector) for Dataplex.

### Prepare your Oracle environment:

1. Create a user in the Oracle instance(s) which will be used by Dataplex to connect and extract metadata about tables and views. The user requires at minimum the following Oracle privileges and roles: 
    * CONNECT and CREATE SESSION
    * SELECT on DBA_OBJECTS
    * SELECT on all schemas for which metadata needs to be extracted
2. Add the password for the user to the Google Cloud Secret Manager in your project and note the Secret ID (format is: projects/[project-number]/secrets/[secret-name])

### Parameters
The Oracle connector takes the following parameters:
|Parameter|Description|Required/Optional|
|---------|------------|-------------|
|target_project_id|Value is GCP Project ID/Project Number, or 'global'. Used in the generated Dataplex Entry, Aspects and AspectTypes|REQUIRED|
|target_location_id|GCP Region ID, or 'global'. Used in the generated Dataplex Entry, Aspects and AspectTypes|REQUIRED|
|target_entry_group_id|Dataplex Entry Group ID to use in the generated data|REQUIRED|
|host|Oracle server to connect to|REQUIRED|
|port|Oracle server port (usually 1521)|REQUIRED|
|service|Oracle service to connect to. **One of either service or sid must be specified**|
|sid|Oracle SID (Service Identifier). **One of either service or sid must be specified**|
|user|Oracle Username to connect with|REQUIRED|
|password-secret|GCP Secret Manager ID holding the password for the Oracle user. Format: projects/[PROJ]/secrets/[SECRET]|REQUIRED|
|output_bucket|GCS bucket where the output file will be stored|REQUIRED|
|output_folder|Folder in the GCS bucket where the export output file will be stored|REQUIRED|

## Running the connector
There are three ways to run the connector:
1) [Run the script directly from the command line](###running-from-the-command-line) (extract metadata to GCS only)
2) [Run as a container via a Dataproc Serverless job](###build-a-container-and-extract-metadata-with-a-dataproc-serverless-job) (extract metadata to GCS only)
3) [Schedule and run as a container via Workflows](###schedule-end-to-end-metadata-extraction-and-import-using-google-cloud-workflows) (End-to-end. Extracts metadata into GCS and imports into Dataplex)

### Running from the command line

The metadata connector can be run ad-hoc from the command line for development or testing by directly executing the main.py script.

#### Prepare the environment:
1. Download **ojdbc11.jar** [from Oracle](https://www.oracle.com/database/technologies/appdev/jdbc-downloads.html)
2. Edit the SPARK_JAR_PATH variable in [oracle_connector.py](src/oracle_connector.py) to match the location of the jar file
3. Ensure a Java Runtime Environment (JRE) is installed in your environment
4. Install PySpark: `pip3 install pyspark`
5. Install all dependencies from the requirements.txt file with `pip3 install -r requirements.txt`
6. If you don't have one set up already, create a Python virtual environment to isolate the connector.
    See [here](https://www.freecodecamp.org/news/how-to-setup-virtual-environments-in-python/) for more details but the TL;DR instructions are to run the following in your home directory:
    ```
    pip install virtualenv
    python -m venv myvenv
    source myvenv/bin/activate
    ```
7. Ensure you have a clear network path from the machine where you will run the script to the target database server

#### Required IAM Roles
- roles/secretmanager.secretAccessor
- roles/storage.objectUser

Before you run the script ensure you session is authenticated as a user which has these roles at minimum (ie using ```gcloud auth application-default login```)

To execute the metadata extraction run the following command (substituting appropriate values for your environment):

```shell 
python3 main.py \
--target_project_id my-gcp-project-id \
--target_location_id us-central1 \
--target_entry_group_id oracledbs \
--host the-oracle-server \
--port 1521 \
--user dataplexagent \
--password-secret projects/73819994526/secrets/dataplexagent_oracle \
--service XEPDB1 \
--output_bucket dataplex_connectivity_imports \
--output_folder oracle
```

#### Output:
The connector generates a metadata extract in JSONL format as described [in the documentation](https://cloud.google.com/dataplex/docs/import-metadata#metadata-import-file). A sample output from the Oracle connector can be found [here](sample/oracle_output_sample.jsonl)

### Build a container and extract metadata with a Dataproc Serverless job:

To build a Docker container for the connector (one-time task) and run the extraction process as a Dataproc Serverless job:

#### Build the container

Ensure the user you run the script with has /artifactregistry.repositories.uploadArtifacts on the artficate registry in your project 

1. Ensure you are authenticated to your Google Cloud account by running ```gcloud auth login```
2. chmod a+x build_and_push_docker.sh to make the script executuable
2. Edit ```build_and_push_docker.sh``` and set PROJECT_ID and REGION_ID to the appropriate values for your project
2. Run```build_and_push_docker.sh``` to build the Docker container and store it in Artifact Registry. This process can take several minutes.
3. Upload the **odjcb11.jar** file to a Google Cloud Storage location (add this path to the **--jars** parameter below)
4. Create a GCS bucket which will be used for Dataproc Serverless as a working directory (add to the **--deps-bucket** parameter below)

#### Submitting a metadata extraction job to Dataproc serverless:
Once the container is built you can run the metadata extract with the following command (substituting appropriate values for your environment). 

#### Required IAM Roles|Parameter|Description|Required/Optional|
The service account you submit for the job using **--service-account** below needs to have the following IAM roles:

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

You can use this [script](scripts/grant_SA_dataproc_roles.sh) to grant the roles to your service account

```shell
gcloud dataproc batches submit pyspark \
    --project=my-gcp-project-id \
    --region=us-central1 \
    --batch=0001 \
    --deps-bucket=dataplex-metadata-collection-bucket \  
    --container-image=us-central1-docker.pkg.dev/my-gcp-project-id/docker-repo/oracle-pyspark@sha256:dab02ca02f60a9e12769999191b06d859b947d89490d636a34fc734d4a0b6d08 \
    --service-account=440199992669-compute@developer.gserviceaccount.com \
    --jars=gs://gcs/path/to/ojdbc11.jar  \
    --network=Your-Network-Name \
    main.py \
--  --target_project_id my-gcp-project-id \
      --target_location_id us-central1	\
      --target_entry_group_id myEntryGroup \
      --host the-oracle-server \
      --port 1521 \
      --user dataplexagent \
      --password-secret projects/73819994526/secrets/dataplexagent_oracle \
      --service XEPDB1 \
      --output_bucket gcs_output_bucket_path \
      --output_folder oracle
```

See the documentatrion for [gcloud dataproc batches submit pyspark](https://cloud.google.com/sdk/gcloud/reference/dataproc/batches/submit/pyspark) for more information

### Schedule end-to-end metadata extraction and import using Google Cloud Workflows

To run an end-to-end metadata extraction and import process, run the container via Google Cloud Workflows. 

Follow the Dataplex documentation here: [Import metadata from a custom source using Workflows ](https://cloud.google.com/dataplex/docs/import-using-workflows-custom-source)


## Manually initiating a metadata import file into Dataplex

To import a metadata import file into Dataplex call the Import API with the following:

```http
POST https://dataplex.googleapis.com/v1/projects/PROJECT_NUMBER/locations/LOCATION_ID/metadataJobs?metadataJobId=METADATA_JOB_ID
```

See the [Dataplex documetation](https://cloud.google.com/dataplex/docs/import-metadata#import-metadata) for full instructions about importing metadata.
