# Snowflake Connector

This connector extracts metadata from Snowflake to BigQuery Universal Catalog.

### Target objects and schemas:

The connector extracts metadata for the following database objects:
* Tables
* Views

### Parameters
The Snowflake connector takes the following parameters:
|Parameter|Description|Required/Optional|
|---------|------------|-------------|
|target_project_id|Google Cloud Project ID. Used in the generated metadata and indicates the project metadata file will be imported to|REQUIRED|
|target_location_id|Google Cloud Region ID, or 'global'. Used in the generated metadata and indicates region where Entries are associated|REQUIRED|
|target_entry_group_id|Dataplex Entry Group ID under which Entries will be imported|REQUIRED|
|account|Snowflake account to connect to|REQUIRED|
|user|Snowflake username to connect with|REQUIRED|
|authentication|Authentication method: password or oauth (default is 'password')|OPTIONAL
|password_secret|GCP Secret Manager ID holding the password for the Snowflake user. Format: projects/[PROJ]/secrets/[SECRET]|REQUIRED if using password auth|
|token|Token for oauth authentication.|REQUIRED if using oauth authentication|
|database|Snowflake database to connect to|REQUIRED|
|warehouse|Snowflake warehouse to connect to|OPTIONAL|
|output_bucket|GCS bucket where the output file will be stored|REQUIRED|
|output_folder|Folder in the GCS bucket where the export output file will be stored|OPTIONAL|

### Prepare your Snowflake environment:

Best practise is to connect to the database using a dedicated user with the minimum privileges required to extract metadata. 

 The user for connecting should be granted a Security Role with the following privileges for the database and schemas, tables and views for which metadata needs to be extracted:
```sql
grant usage on warehouse <warehouse_name> to role <role_name>;
grant usage on database <database_name> to role <role_name>;
grant usage on all schemas in database <database_name> to role <role_name>;
grant references on all tables in schema <schema_name> to role <role_name>;
grant references on all views in schema <schema_name> to role <role_name>;
```

2. Add the password for the snowflake user to the Google Cloud Secret Manager in your project and note the Secret ID (format is: projects/[project-number]/secrets/[secret-name])

## Running the connector
There are three ways to run the connector:
1) [Run the script directly from the command line](###running-from-the-command-line) (extract metadata to GCS only)
2) [Run as a container via a Dataproc Serverless job](###build-a-container-and-extract-metadata-with-a-dataproc-serverless-job) (extract metadata to GCS only)
3) [Schedule and run as a container via Workflows](###schedule-end-to-end-metadata-extraction-and-import-using-google-cloud-workflows) (End-to-end. Extracts metadata into GCS and imports into Dataplex)

## Running the connector from the command line

The metadata connector can be run from the command line by executing the main.py script.

#### Prerequisites

The following tools must be installed in order to run the connector:

* Python 3.x. [See here for installation instructions](https://cloud.google.com/python/docs/setup#installing_python)
* Java Runtime Environment (JRE)
    ```bash
    sudo apt install default-jre
    ```
* A python Virtual Environment. Follow the instructions [here](https://cloud.google.com/python/docs/setup#installing_and_using_virtualenv) to create and activate your environment.
* Install PySpark
    ```bash
    pip3 install pyspark
    ```
* You must run the script with a user that is authenticated to Google Cloud in order to access services there.  You can use [Application Default Credentials](https://cloud.google.com/sdk/gcloud/reference/auth/application-default/login) for the connector to access Google APIs. 

(To use gcloud you may need to [install the Google Cloud SDK](https://cloud.google.com/sdk/docs/install):

```bash
    gcloud auth application-default login
```
The authenticated user must have the following roles for the project: roles/secretmanager.secretAccessor, roles/storage.objectUser

#### Set up
* Ensure you are in the root directory of the connector
    ```bash
    cd sql-server-connector
    ```
* Download the following jars [from Maven](https://repo1.maven.org/maven2/net/snowflake/)
    * [snowflake-jdbc-3.19.0.jar](https://repo1.maven.org/maven2/net/snowflake/snowflake-jdbc/3.19.0/)
    * [spark-snowflake_2.12-3.1.1.jar](https://repo1.maven.org/maven2/net/snowflake/spark-snowflake_2.12/3.1.1/)
** Install all python dependencies 
    ```bash
    pip3 install -r requirements.txt
    ```

#### Run the connector
To execute the metadata extraction run the following, substituting appropriate values for your environment as needed:

```shell 
python3 main.py \
--target_project_id my-gcp-project \
--target_location_id us-central1 \
--target_entry_group_id snowflake \
--account RXXXXXA-GX00020 \
--user dataplex_snowflake_user \
--password-secret projects/499965349999/secrets/snowflake \
--database my_snowflake_database \
--warehouse COMPUTE_WH \
--output_bucket my-gcs-bucket
--output_folder snowflake
```

### Connector Output:
The connector generates a metadata extract file in JSONL format as described [in the documentation](https://cloud.google.com/dataplex/docs/import-metadata#metadata-import-file) and stores the file in the local 'output' directory within the connector, as well as uploading it to a Google Cloud Storage bucket as specified in --output_bucket and --output_folder (unless in --local-output_only mode)

A sample output from the SQL Server connector can be found [here](sample/sqlserver_output_sample.jsonl).


## Importing metadata into BigQuery Universal Catalog

To manually import a metadata import file into BigQuery Universal Catalog see the [documetation](https://cloud.google.com/dataplex/docs/import-metadata#import-metadata) for full instructions about calling the API.
The [samples](/samples) directory contains a sample metadata file and request file you can use to import into the catalog.

See below for the section on using Google Workflows to create an end-to-end integration which both extracts metadata and imports it on a regular schedule.


## Build a container and running the connector using Dataproc Serverless

Building a Docker container for the connector allows it to be run from a variety of Google Cloud services including [Dataproc Serverless](https://cloud.google.com/dataproc-serverless/docs).

### Building the container (one-time task)

1. Ensure docker is installed in your environment.
2. Edit [build_and_push_docker.sh](build_and_push_docker.sh) and set the PROJECT_ID AND REGION_ID
3. Ensure the user that runs the script is authenticated with a Google Cloud identify which has (Artifact Registry Writer)[https://cloud.google.com/artifact-registry/docs/access-control#roles] role on the Artfiact Registry in your project.
4. Make the script executable and run:
    ```bash
    chmod a+x build_and_push_docker.sh
    ./build_and_push_docker.sh
    ``` 

    This will build a Docker container called **bq-catalog-sqlserver-pyspark** and store it in Artifact Registry. 
    This process can take take up to 10 minutes.

### Submitting a metadata extraction job to Dataproc Serverless:

Before you run please ensure:
1. You upload the jdbc jar file to a Google Cloud Storage location and use the path to this in the **--jars** parameter below.
2. Create a GCS bucket which will be used for Dataproc Serverless as a working directory (add to the **--deps-bucket** parameter below.
3. The service account you run the job with using **--service-account** below has the IAM roles described [here](https://cloud.google.com/dataplex/docs/import-using-workflows-custom-source#required-roles).
You can use this [script](../common_scripts/grant_SA_dataproc_roles.sh) to grant the required roles to your service account.

Run the containerised metadata connector using the following command, substituting appropriate values for your environment: 

```shell
gcloud dataproc batches submit pyspark \
    --project=my-gcp-project-id \
    --region=us-central1 \
    --batch=0001 \
    --deps-bucket=dataplex-metadata-collection-bucket \  
    --container-image=us-central1-docker.pkg.dev/my-gcp-project-id/docker-repo/snowflake-pyspark@sha256:dab02ca02f60a9e12769999191b06d859b947d89490d636a34fc734d4a0b6d08 \
    --service-account=440199992669-compute@developer.gserviceaccount.com \
    --network=Your-Network-Name \
    main.py \
    --target_project_id my-gcp-project \
    --target_location_id us-central1 \
    --target_entry_group_id snowflake \
    --account RXXXXXA-GX00020 \
    --user snowflakeuser \
    --password-secret projects/499965349999/secrets/snowflake \
    --database SNOWFLAKE_SAMPLE_DATA \
    --output_bucket my-gcs-bucket
```

See [the documentation](https://cloud.google.com/sdk/gcloud/reference/dataproc/batches/submit/pyspark) for more information about Dataproc Serverless pyspark jobs

## Scheduling end-to-end metadata extraction and import into BigQuery Universal Catalog with Google Cloud Workflows

An an end-to-end metadata extraction and import process can run via Google Cloud Workflows. 

Follow the documentation here: [Import metadata from a custom source using Workflows](https://cloud.google.com/dataplex/docs/import-using-workflows-custom-source) and use [this yaml file](https://github.com/GoogleCloudPlatform/cloud-dataplex/blob/main/managed-connectivity/cloud-workflows/byo-connector/templates/byo-connector.yaml) as a template.

A sample input for SQL Server import via Google Workflows is included in the [workflows](workflows) directory