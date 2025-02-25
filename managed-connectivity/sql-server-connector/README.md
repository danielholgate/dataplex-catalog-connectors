# SQL Server Connector

This custom connector exports metadata for tables and views from SQL Server databases to create a [metadata import file](https://cloud.google.com/dataplex/docs/import-metadata#components) which can be imported into Google Dataplex. 

The connector will connect to the instance and database specified and extract metadata for all schemas other than the following:


You can read more about custom connectors in the documentation for [Dataplex Managed Connectivity framework](https://cloud.google.com/dataplex/docs/managed-connectivity-overview) and [Developing a custom connector](https://cloud.google.com/dataplex/docs/develop-custom-connector) for Dataplex.

## Prepare your SQL Server environment:

1. Create a user in the SQL Server instance(s) which will be used by Dataplex to connect and extract metadata about tables and views. This user requires the following SQL Server permissions: 
    * CONNECT to the database
    * SELECT on all tables in the target database(s)
2. Add the password for the user to the Google Cloud Secret Manager in your project and note the Secret ID (format is: projects/[project-number]/secrets/[secret-name])

### Parameters
The SQL Server connector takes the following parameters:
|Parameter|Description|Required/Optional|
|---------|------------|-------------|
|target_project_id|GCP Project ID or number which will be used in the generated Dataplex Entry, Aspects and AspectTypes|REQUIRED|
|target_location_id|GCP region ID which will be used in the generated Dataplex Entry, Aspects and AspectTypes|REQUIRED|
|target_entry_group_id|The Dataplex Entry Group ID to be used in the metadata|REQUIRED|
|host|SQL Server server to connect to|REQUIRED|
|port|SQL Server host port (usually 1443)|REQUIRED|
|instancename|The SQL Server instance to connect to. If not provided the default instance will be used|OPTIONAL
|database|The SQL Server database name|REQUIRED|
|user|Username to connect with|REQUIRED|
|password-secret|GCP Secret Manager ID holding the password for the user. Format: projects/PROJ/secrets/SECRET|REQUIRED|
|output_bucket|GCS bucket where the output file will be stored|REQUIRED|
|output_folder|Folder within the GCS bucket where the export output file will be stored|REQUIRED|

### Running the connector
There are three ways to run the connector:
1) [Run the script directly from the command line](###running-from-the-command-line) (extract metadata into GCS)
2) [Run as a container via a Dataproc Serverless job](###submitting-a-metadata-extraction-job-to-dataproc-serverless) (extract metadata into GCS)
3) [Schedule and run as a container via Workflows](###schedule-an-end-to-end-metadata-extract-and-import-with-workflows) ] (End-to-end. Extract metadata into GCS and import metadata into Dataplex)

## Running from the command line

The metadata connector can be run ad-hoc from the command line for development or testing by directly executing the main.py script.

### Prepare the environment:
1. Download the **mssql-jdbc** jar file [from Microsoft](https://docs.microsoft.com/en-us/sql/connect/jdbc/download-microsoft-jdbc-driver-for-sql-server?view=sql-server-2022) and include in the same folder as the other python files for this connector
2. Edit the SPARK_JAR_PATH variable in [sqlserver_connector.py](src/sqlserver_connector.py) to match the location of the jar file
3. Ensure a Java Runtime Environment (JRE) is installed in your environment
4. Install PySpark: `pip3 install pyspark`
5. Install all dependencies from the requirements.txt file with `pip3 install -r requirements.txt`
6. Ensure you have a clear network path from the machine where you will run the script to the target database server

### Required IAM Roles
- roles/secretmanager.secretAccessor
- roles/storage.objectUser

Before you run the script ensure you session is authenticated as a user which has these roles at minimum (ie using ```gcloud auth application-default login```)

To execute the metadata extraction run the following command (substituting appropriate values for your environment):

```shell 
python3 main.py \
--target_project_id my-gcp-project-id \
--target_location_id us-central1 \
--target_entry_group_id sqlserverdbs \
--host the-sqlserver-server \
--port 1433 \
--database testdb \
--user dataplexagent \
--password-secret projects/73813454526/secrets/dataplexagent_sqlserver \
--database AdventureWorksDW2019 \
--output_bucket dataplex_connectivity_imports \
--output_folder sqlserver
```

### Output:
The connector generates a metadata extract file in JSONL format as described [in the documentation](https://cloud.google.com/dataplex/docs/import-metadata#metadata-import-file). A sample output from the SQL Server connector can be found [here](sample/sqlserver_output_sample.jsonl)

## Build a container and extract metadata using [Dataproc Serverless](https://cloud.google.com/dataproc-serverless/docs)

To build a Docker container for the connector and run the extraction process as a Dataproc serverless job:

### Building the container (one-time task)
1. Run the script ```build_and_push_docker.sh``` to build the Docker container and store it in Artifact Registry. This process can take take up to 10 minutes.
2. Upload the **mssql-jdbc** jar file to a Google Cloud Storage location (add this path to the **--jars** parameter below)
3. Create a GCS bucket which will be used for Dataproc Serverless as a working directory (add to the **--deps-bucket** parameter below)

### Submitting a metadata extraction job to Dataproc serverless:
Once the container is built you can run the metadata extract with the following command (substituting appropriate values for your environment). 

Note the service account you submit for the job with --service-account needs the following roles:

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
    --container-image=us-central1-docker.pkg.dev/my-gcp-project-id/docker-repo/sqlserver-pyspark@sha256:dab02ca02f60a9e12767996191b06d859b947d89490d636a34fc734d4a0b6d08 \
    --service-account=440165342669-compute@developer.gserviceaccount.com \
    --jars=[gs://path/to/mssql-jdbc-9.4.1.jre8.jar]  \
    --network=[Your-Network-Name] \
    main.py \
--  --target_project_id my-gcp-project-id \
      --target_location_id us-central1	\
      --target_entry_group_id XXX \
      --host the-sqlserver-server \
      --port 1433 \
      --user dataplexagent \
      --password-secret projects/73813454526/dataplexagent_sqlserver \
      --database AdventureWorksDW2019 \
      --output_bucket gs://dataplex_connectivity_imports \
      --output_folder sqlserver
```

## Schedule an end-to-end metadata extract and import with Workflows

Assumes you have already built the container. To run an end-to-end metadata extraction and import process via Google Workflows follow the Dataplex documentation here: [Import metadata from a custom source using Workflows ](https://cloud.google.com/dataplex/docs/import-using-workflows-custom-source)

## Manually initiating a metadata import file into Dataplex

To import a metadata import file into Dataplex call the Import API with the following:

```http
POST https://dataplex.googleapis.com/v1/projects/PROJECT_NUMBER/locations/LOCATION_ID/metadataJobs?metadataJobId=METADATA_JOB_ID
```

See the [Dataplex documetation](https://cloud.google.com/dataplex/docs/import-metadata#import-metadata) for full instructions about importing metadata.
