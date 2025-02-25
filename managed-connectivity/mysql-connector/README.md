# Mysql Connector

This custom connector exports metadata for tables and views from mysql databases to create a [metadata import file](https://cloud.google.com/dataplex/docs/import-metadata#components) which can be imported into Google Dataplex. 
You can read more about custom connectors in the documentation for [Dataplex Managed Connectivity framework](https://cloud.google.com/dataplex/docs/managed-connectivity-overview) and [Developing a custom connector](https://cloud.google.com/dataplex/docs/develop-custom-connector) for Dataplex.

### Prepare your Mysql environment:

1. Create a user in the Mysql instance(s) which will be used by Dataplex to connect and extract metadata about tables and views. The user requires at minimum the following Mysql privileges: 
    * SELECT on information_schema.tables
    * SELECT on information_schema.columns
    * SELECT on information_schema.views
2. Add the password for the user to the Google Cloud Secret Manager in your project and note the Secret ID (format is: projects/[project-number]/secrets/[secret-name])

### Parameters
The Mysql connector takes the following parameters:
|Parameter|Description|Mandatory/Optional|
|---------|------------|-------------|
|target_project_id|Value is GCP Project ID/Project Number, or 'global'. Used in the generated Dataplex Entry, Aspects and AspectTypes|MANDATORY|
|target_location_id|GCP Region ID, or 'global'. Used in the generated Dataplex Entry, Aspects and AspectTypes|MANDATORY|
|target_entry_group_id|Dataplex Entry Group ID to use in the generated data|MANDATORY|
|host|Mysql server to connect to|MANDATORY|
|port|Mysql server port (usually 3306)|MANDATORY|
|database|Mysql database to connect to|MANDATORY|
|user|Mysql Username to connect with|MANDATORY|
|password-secret|GCP Secret Manager ID holding the password for the Mysql user. Format: projects/[PROJ]/secrets/[SECRET]|MANDATORY|
|output_bucket|GCS bucket where the output file will be stored (do not include gs:// prefix)|MANDATORY|
|output_folder|Folder in the GCS bucket where the export output file will be stored|MANDATORY|

## Running the connector
There are three ways to run the connector:
1) [Run the script directly from the command line](###running-from-the-command-line) (extract metadata to GCS only)
2) [Run as a container via a Dataproc Serverless job](###build-a-container-and-extract-metadata-with-a-dataproc-serverless-job) (extract metadata to GCS only)
3) [Schedule and run as a container via Workflows](###schedule-end-to-end-metadata-extraction-and-import-using-google-cloud-workflows) (End-to-end. Extracts metadata into GCS and imports into Dataplex)

### Running from the command line

The metadata connector can be run ad-hoc from the command line for development or testing by directly executing the main.py script.

#### Prepare the environment:
1. Download **mysql-connector-j-9.2.0.jar** [from MySQL](https://dev.mysql.com/downloads/connector/j/?os=26)
2. Edit the SPARK_JAR_PATH variable in [mysql_connector.py](src/mysql_connector.py) to match the location of the jar file
3. Ensure a Java Runtime Environment (JRE) is installed in your environment
4. Install PySpark: `pip3 install pyspark`
5. Install all dependencies from the requirements.txt file with `pip3 install -r requirements.txt`
6. Create a Python virtual environment to isolate the connector environment.
    See [here](https://www.freecodecamp.org/news/how-to-setup-virtual-environments-in-python/) for more details but the TLDR; instructions are to run the following in your home directory:
    ```
    pip install virtualenv
    python -m venv myvenv
    source myvenv/bin/activate
    ```
6. Ensure you have a clear network path from the machine where you will run the script to the target database server

#### Required IAM Roles
- roles/secretmanager.secretAccessor
- roles/storage.objectUser

Before you run the script ensure you session is authenticated as a user which has these roles at minimum (ie using ```gcloud auth application-default login```)

To execute the metadata extraction run the following command (substituting appropriate values for your environment):

```shell 
python3 main.py \
--target_project_id my-gcp-project-id \
--target_location_id us-central1 \
--target_entry_group_id mysql \
--host the-mysql-server \
--port 3306 \
--user dataplexagent \
--password-secret projects/73819994526/secrets/dataplexagent_mysql \
--database employees \
--output_bucket dataplex_connectivity_imports \
--output_folder mysql
```

#### Output:
The connector generates a metadata extract in JSONL format as described [in the documentation](https://cloud.google.com/dataplex/docs/import-metadata#metadata-import-file). A sample output from the Mysql connector can be found [here](sample/mysql_output_classicmodels_db.jsonl)

### Build a container and extract metadata with a Dataproc Serverless job:

To build a Docker container for the connector (one-time task) and run the extraction process as a Dataproc Serverless job:

#### Build the container

Ensure the user you run the script with has /artifactregistry.repositories.uploadArtifacts on the artficate registry in your project 

1. Ensure you are authenticated to your Google Cloud account by running ```gcloud auth login```
2. chmod a+x build_and_push_docker.sh to make the script executuable
2. Edit ```build_and_push_docker.sh``` and set PROJECT_ID and REGION_ID to the appropriate values for your project
2. Run```build_and_push_docker.sh``` to build the Docker container and store it in Artifact Registry. This process can take several minutes.
3. Create a GCS bucket which will be used for Dataproc Serverless as a working directory (add to the **--deps-bucket** parameter below)

#### Submitting a metadata extraction job to Dataproc serverless:
Once the container is built you can run the metadata extract with the command below (substituting appropriate values for your environment). 

#### Required IAM Roles
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
    --deps-bucket=dataplex-metadata-collection-bucket  \
    --container-image=us-central1-docker.pkg.dev/my-gcp-project-id/docker-repo/mysql-pyspark@sha256:dab02ca02f60a9e12769999191b06d859b947d89490d636a34fc734d4a0b6d08 \
    --service-account=440199992669-compute@developer.gserviceaccount.com \
    --network=Your-Network-Name \
    main.py \
--  --target_project_id my-gcp-project-id \
      --target_location_id us-central1	\
      --target_entry_group_id mysql \
      --host the-mysql-server \
      --port 3306 \
      --user dataplexagent \
      --password-secret projects/73819994526/secrets/dataplexagent_mysql \
      --database employees \
      --output_bucket gcs_output_bucket_path \
      --output_folder mysql
```

See the documentatrion for [gcloud dataproc batches submit pyspark](https://cloud.google.com/sdk/gcloud/reference/dataproc/batches/submit/pyspark) for more information

### Schedule end-to-end metadata extraction and import using Google Cloud Workflows

To run an end-to-end metadata extraction and import process, run the container via Google Cloud Workflows. 

Follow the Dataplex documentation here: [Import metadata from a custom source using Workflows ](https://cloud.google.com/dataplex/docs/import-using-workflows-custom-source)


## Manually initiating a metadata import file into Dataplex

To import a metadata import file into Dataplex call the Import API with the following:

```http
POST https://dataplex.googleapis.com/v1/projects/PROJECT_NUMBER/locations/LOCATION_ID/metadataJobs?metadataJobId=METADATA_JOB_ID

See the [Dataplex documetation](https://cloud.google.com/dataplex/docs/import-metadata#import-metadata) for full instructions about importing metadata.
