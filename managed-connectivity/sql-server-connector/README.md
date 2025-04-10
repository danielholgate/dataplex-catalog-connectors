# SQL Server Connector

This connector extracts metadata from SQL Server to Google Cloud Dataplex Catalog.

### Target objects and schemas:

The connector extracts metadata for the following database objects:
* Tables
* Views

## Parameters
The SQL Server connector takes the following parameters:
|Parameter|Description|Default Value|Required/Optional|
|---------|------------|--|-------------|
|target_project_id|GCP Project ID of project used in the generated Dataplex entries and where metadata will be associated||REQUIRED|
|target_location_id|GCP Region ID of project used in the generated Dataplex entries and where metadata will be associated||REQUIRED|
|target_entry_group_id|Dataplex Entry Group ID used in generated metadata||REQUIRED|
|host|SQL Server host to connect to||REQUIRED|
|port|SQL Server host port|1433|OPTIONAL|
|instancename|The SQL Server instance to connect to. If not provided the default instance will be used||OPTIONAL
|database|The SQL Server database name||REQUIRED|
|login_timeout|Allowed timeout (seconds) to establish connection to SQL Server|0 (=use JDBC driver default)|OPTIONAL
|encrypt|True/False Encrypt connection to database|True|OPTIONAL
|trust_server_certificate|Trust SQL Server TLS certificate or not|True|OPTIONAL
|hostname_in_certificate|domain of host certificate||OPTIONAL
|user|Username to connect with||REQUIRED|
|password_secret|GCP Secret Manager ID holding the password for the user||REQUIRED|
|output_bucket|GCS bucket where the output file will be stored||REQUIRED|
|output_folder|Folder in the GCS bucket where the export output file will be stored||OPTIONAL|

## Prepare your SQL Server environment:

Best practise is to connect to the database using a dedicated user with the minimum privileges required to extract metadata. 

1. Create a user in SQL Server with at minmum the following privileges:
    * CONNECT to database
    * SELECT on sys.columns
    * SELECT on sys.tables
    * SELECT on sys.types

2. Add the password for the user to the Google Cloud Secret Manager in your project and note the Secret ID (format is: projects/[project-number]/secrets/[secret-name])

### Running the connector from the command line

The metadata connector can be run from the command line by executing the main.py script.

### Prepare the environment:

1. Download the mssql-jdbc-12.10.0.jre11.jar file [from Microsoft](https://docs.microsoft.com/en-us/sql/connect/jdbc/download-microsoft-jdbc-driver-for-sql-server?view=sql-server-2022)
2. Ensure a Java Runtime Environment (JRE) is installed in your environment
3. [Install Python](https://cloud.google.com/python/docs/setup#installing_python)
4. Follow the instructions [here](https://cloud.google.com/python/docs/setup#installing_and_using_virtualenv) to create a Python virtual environment to isolate the connector project dependencies
5. Install PySpark
    ```bash
    pip3 install pyspark
    ```
6. Install all remaining dependencies from the requirements.txt file 
    ```bash
    pip3 install -r requirements.txt
    ```
7.  In development or testing environments set the default credentials for the connector to access Google APIs:
    ```bash
    gcloud auth application-default login
    ```
Note: The identity requires the following IAM Roles:
- roles/secretmanager.secretAccessor
- roles/storage.objectUser

See [here](https://cloud.google.com/sdk/gcloud/reference/auth/application-default/login) for more details. To use gcloud you may need to [install the Google Cloud SDK](https://cloud.google.com/sdk/docs/install)

8. Ensure you have a clear network path from the machine where you will run the script to the target database server

To execute the metadata extraction run the following command (substituting appropriate values for your environment):

```shell 
python3 main.py \
--target_project_id my-gcp-project-id \
--target_location_id us-central1 \
--target_entry_group_id sqlserver \
--host the-sqlserver-server \
--port 1433 \
--database dbtoextractfrom \
--user dataplexagent \
--password-secret projects/73899954526/secrets/dataplexagent_sqlserver \
--output_bucket dataplex_connectivity_imports \
--output_folder sqlserver
```

## Connector Output:
The connector generates a metadata extract file in JSONL format as described [in the documentation](https://cloud.google.com/dataplex/docs/import-metadata#metadata-import-file). A sample output from the SQL Server connector can be found [here](sample/sqlserver_output_sample.jsonl)



## Manually running a metadata import into Dataplex

To manually import a metadata import file into Dataplex, see the [Dataplex documetation](https://cloud.google.com/dataplex/docs/import-metadata#import-metadata) for full instructions about calling the API.
The [samples](/samples) directory contains a sample metadata import file and request file for callng the API.

You can also use the Google Workflows and proivded YAML file to create an end-to-end integration which extracts metadata and imports it on a regular schedule.

## Build a container and run the connector using Dataproc Serverless

Building a Docker container for the connector allows it to be run from a variety of Google Cloud services including [Dataproc Serverless](https://cloud.google.com/dataproc-serverless/docs).

### Building the container (one-time task)

1. Ensure docker is installed in your environment.
2. Edit [build_and_push_docker.sh](build_and_push_docker.sh) and set the PROJECT_ID AND REGION_ID
3. Ensure the user that runs the script has artifactregistry.repositories.uploadArtifacts privilege on the Artfiact Registry in your project in order to create the new container image.
4. Make the script executable and run:
    ```bash
    chmod a+x build_and_push_docker.sh
    ./build_and_push_docker.sh
    ``` 

    This will build a Docker container called **dataplex-sqlserver-pyspark** and store it in Artifact Registry. 
    This process can take take up to 10 minutes.

### Submitting a metadata extraction job to Dataproc Serverless:

Before you run please ensure:
1. You upload the **mssql-jdbc** jar file to a Google Cloud Storage location and use the path to this in the **--jars** parameter below.
2. Create a GCS bucket which will be used for Dataproc Serverless as a working directory (add to the **--deps-bucket** parameter below.
3. The service account you run the job with using **--service-account** below has the IAM roles described [here](https://cloud.google.com/dataplex/docs/import-using-workflows-custom-source#required-roles).
You can use this [script](../common_scripts/grant_SA_dataproc_roles.sh) to grant the required roles to your service account.

Run the containerised metadata connector using the following command, substituting appropriate values for your environment: 
```shell
gcloud dataproc batches submit pyspark \
    --project=my-gcp-project-id \
    --region=us-central1 \
    --batch=0001 \
    --deps-bucket=dataplex-metadata-collection-usc1 \  
    --container-image=us-central1-docker.pkg.dev/the-project-id/docker-repo/dataplex-sqlserver-pyspark:latest \
    --service-account=499995342669-compute@developer.gserviceaccount.com \
    --jars=gs://path/to/mssql-jdbc-9.4.1.jre8.jar  \
    --network=[Your-Network-Name] \
    main.py \
--  --target_project_id my-gcp-project-id \
    --target_location_id us-central1 \
    --target_entry_group_id sqlserver \
    --host the-sqlserver-server \
    --port 1433 \
    --database dbtoextractfrom \
    --user dataplexagent \
    --password-secret projects/73899954526/secrets/dataplexagent_sqlserver \
    --output_bucket dataplex_connectivity_imports \
    --output_folder sqlserver
```
See [the documentation](https://cloud.google.com/sdk/gcloud/reference/dataproc/batches/submit/pyspark) for more information about Dataproc Serverless pyspark jobs

## Schedule end-to-end metadata extraction and import into Dataplex Catalog using Google Cloud Workflows

To run an end-to-end metadata extraction and import process, run the container via Google Cloud Workflows. 

Follow the Dataplex documentation here: [Import metadata from a custom source using Workflows](https://cloud.google.com/dataplex/docs/import-using-workflows-custom-source) and use [this yaml file](https://github.com/GoogleCloudPlatform/cloud-dataplex/blob/main/managed-connectivity/cloud-workflows/byo-connector/templates/byo-connector.yaml) as a template.
