# SQL Server Connector

This connector extracts metadata from SQL Server to BigQuery universal catalog.

The code is based on the [Managed Connectivity framework](https://cloud.google.com/dataplex/docs/managed-connectivity-overview). See [here](https://cloud.google.com/dataplex/docs/develop-custom-connector) for more information about custom connectors.

### Target objects and schemas:

Metadata for the following database objects is extracted:
* Tables
* Views

## Parameters
The connector accepts the following parameters:
|Parameter|Description|Default Value|Required/Optional|
|---------|------------|--|-------------|
|target_project_id|Google Cloud Project ID of project used in the generated entries||REQUIRED|
|target_location_id|Google Cloud Region ID used in the generated entries||REQUIRED|
|target_entry_group_id|ID of the [Entry Group](https://cloud.google.com/dataplex/docs/catalog-overview#catalog-model) to be used in generated metadata||REQUIRED|
|host|SQL Server host to connect to||REQUIRED|
|port|SQL Server host port|1433|OPTIONAL|
|instancename|The SQL Server instance to connect to|defaultinstance|OPTIONAL
|database|The SQL Server database name||REQUIRED|
|output_bucket|Cloud Storage bucket where the output file will be stored||REQUIRED|
|output_folder|Folder in the Cloud Storage bucket where the export output file will be stored||REQUIRED|
|login_timeout|Time to establish connection to SQL Server (seconds)|0 (=use JDBC driver default)|OPTIONAL
|encrypt|True/False Encrypt connection to database|True|OPTIONAL
|use_ssl|Use SSL for connection? True/False|True|OPTIONAL
|ssl_mode|'prefer','require','allow','verify-ca', or 'verify-full|prefer|OPTIONAL
|trust_server_certificate|Trust SQL Server TLS certificate or not|True|OPTIONAL
|hostname_in_certificate|domain of host certificate||OPTIONAL
|user|User name to connect with||REQUIRED|
|password_secret|[Secret Manager](https://cloud.google.com/security/products/secret-manager) ID holding the password for the user||REQUIRED|
|password|Plain text user password. Use for dev or testing only, for production use --password_secret||REQUIRED|
|jar|Name (or full path to) JDBC jar file to use for connection||OPTIONAL|

## Prepare your SQL Server environment:

Best practise is to connect to the database using a dedicated user with the minimum privileges required to extract metadata. 

1. Create a user in SQL Server with at minimum the following privileges:
    * CONNECT to database
    * SELECT on sys.columns
    * SELECT on sys.tables
    * SELECT on sys.types

2. Add the password for the user to the Secret Manager in your project and note the Secret ID (format is: projects/[project-number]/secrets/[secret-name])

## Set up and run the connector

The metadata connector can be run directly from the command line by executing the main.py script.

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
* You must run the script with a user that is authenticated to Google Cloud in order to access services there.  You can use [Application Default Credentials](https://cloud.google.com/sdk/gcloud/reference/auth/application-default/login) for the connector to access Google APIs. (To use gcloud you may need to [install the Google Cloud SDK](https://cloud.google.com/sdk/docs/install) )

```bash
    gcloud auth application-default login
```
The authenticated user must have the following roles for the project: roles/secretmanager.secretAccessor, roles/storage.objectUser

#### Set up
* Ensure you are in the root directory of the connector
    ```bash
    cd sql-server-connector
    ```
* Download the [mssql-jdbc-12.10.0.jre11.jar](https://github.com/microsoft/mssql-jdbc/releases/download/v12.10.0/mssql-jdbc-12.10.0.jre11.jar) file from the [Microsoft Github repo](https://github.com/microsoft/mssql-jdbc/releases/tag/v12.10.0) and save it in the directory
    * **Note** If you use a different version of the jdbc jar then use the --jar parameter in commands below ie. --jar mssql-jdbc-12.10.2.jre11.jar
* Install all python dependencies 
    ```bash
    pip3 install -r requirements.txt
    ```

#### Run the connector
To execute metadata extraction run the following command, substituting appropriate values for your environment as needed:

```shell 
python3 main.py \
--target_project_id gcp-project-id \
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

### Connector Output:
The connector generates a metadata extract file in JSONL format as described [in the documentation](https://cloud.google.com/dataplex/docs/import-metadata#metadata-import-file) and stores the file locally in the 'output' directory. The connector also uploads the file to the Google Cloud Storage bucket and folder specified in the --output_bucket and --output_folder parameters (unless the --local-output_only parameter is used)

A sample output from the SQL Server connector can be found [here](sample/sqlserver_output_sample.jsonl).


## Import metadata into universal catalog

To manually import a metadata import file into universal catalog see the [documetation](https://cloud.google.com/dataplex/docs/import-metadata#import-metadata) for full instructions about calling the API.
The [samples](/samples) directory contains a sample metadata file and request file you can use to import into the catalog.

See below for the section on using [Workflows](https://cloud.google.com/workflows) to create an end-to-end integration which both extracts metadata and imports it to universal catalog on a regular schedule.


## Build a container and run the connector with Dataproc Serverless

Building a Docker container for the connector allows the connector to be run from a variety of Google Cloud services including [Dataproc Serverless](https://cloud.google.com/dataproc-serverless/docs).

### Build the container (one-time task)

1. Ensure ]docker](https://docs.docker.com/engine/install/) is installed in your environment.
2. Edit [build_and_push_docker.sh](build_and_push_docker.sh) and set the PROJECT_ID AND REGION as appropriate. The container will be stored in Artifact Registry using this information.
3. Ensure the user which runs the script is authenticated as an identify in Google Cloud which has the (Artifact Registry Writer)[https://cloud.google.com/artifact-registry/docs/access-control#roles] IAM role for the Artifact Registry in your project.
4. Make the script executable and run:
    ```bash
    chmod a+x build_and_push_docker.sh
    ./build_and_push_docker.sh
    ``` 

    This will build a container called **universal-catalog-sqlserver-pyspark** and store it in Artifact Registry. 
    This process can take take up to 10 minutes.

### Submit a metadata extraction job to Dataproc Serverless:

Before you submit a job to Dataproc Serverles:
1. Upload the jdbc jar file to Cloud Storage and use the path to the file in the **--jars** parameter below.
2. Create a Cloud Storage bucket which will be used for Dataproc Serverless as a working directory (add to the **--deps-bucket** parameter below.
3. The service account with using **--service-account** below has the IAM roles described [here](https://cloud.google.com/dataplex/docs/import-using-workflows-custom-source#required-roles).
You can use this [script](../common_scripts/grant_SA_dataproc_roles.sh) to grant the required roles to your service account.

Run the containerised metadata connector with the following command, substituting appropriate values for your environment: 
```shell
gcloud dataproc batches submit pyspark \
    --project=gcp-project-id \
    --region=us-central1 \
    --batch=0001 \
    --deps-bucket=dataplex-metadata-collection-usc1 \  
    --container-image=us-central1-docker.pkg.dev/gcp-project-id/docker-repo/universal-catalog-sqlserver-pyspark:latest \
    --service-account=499995342669-compute@developer.gserviceaccount.com \
    --jars=mssql-jdbc-12.10.0.jre11.jar  \
    --network=projects/gcp-project-id/global/networks/default \
main.py \
--  --target_project_id gcp-project-id \
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
See [Dataproc documentation](https://cloud.google.com/sdk/gcloud/reference/dataproc/batches/submit/pyspark) for more information about Dataproc Serverless pyspark jobs

## Schedule end-to-end metadata extraction and import into universal catalog

An end-to-end metadata extraction and import process can set up with Google Cloud Workflows. 

Follow the documentation here: [Import metadata from a custom source using Workflows](https://cloud.google.com/dataplex/docs/import-using-workflows-custom-source) and use [this yaml file](https://github.com/GoogleCloudPlatform/cloud-dataplex/blob/main/managed-connectivity/cloud-workflows/byo-connector/templates/byo-connector.yaml) as a template.

Sample input parameters for an import job with Google Workflows can be found in the [workflows](workflows) directory
