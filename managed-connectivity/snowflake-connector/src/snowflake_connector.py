"""Reads Snowflake using PySpark."""
from typing import Dict
from pyspark.sql import SparkSession, DataFrame
from src.constants import EntryType
from src.connection_jar import SPARK_JAR_PATH

localconfig = []

class SnowflakeConnector:
    """Reads data from Snowflake and returns Spark Dataframes."""

    sfOptions = {}

    def __init__(self, config: Dict[str, str]):
        # PySpark entrypoint
        self._spark = SparkSession.builder.appName("SnowflakeIngestor") \
            .config("spark.jars", SPARK_JAR_PATH) \
            .getOrCreate()

        self._url = f"{config['account']}.snowflakecomputing.com"

        self._sfOptions = {
            "sfURL": self._url,
            "sfUser": config['user'],
            "sfPassword": config['password'],
            "sfDatabase": config['database'],
            "sfWarehouse" : config['warehouse'],
            "sfSchema": "",
            "sfRole": ""
            }

    def _execute(self, query: str) -> DataFrame:
        """A generic method to execute any query."""

        sfOptions = self._sfOptions

        SNOWFLAKE_SOURCE_NAME = "net.snowflake.spark.snowflake"

        return self._spark.read.format(SNOWFLAKE_SOURCE_NAME) \
            .options(**sfOptions) \
            .option("query", query) \
            .load()

    def get_db_schemas(self) -> DataFrame:
        """Query schemas to collect metadata for"""
        query = f"""
        SELECT schema_name FROM information_schema.schemata 
        WHERE schema_name != 'INFORMATION_SCHEMA'
        """
        return self._execute(query)

    def _get_columns(self, schema_name: str, object_type: str) -> str:
        """Gets a list of columns in tables or views in a batch."""
        # Every line here is a column that belongs to the table or to the view.
        # This SQL gets data from ALL the tables in a given schema.
        return (f"SELECT c.table_name, c.column_name,  "
                f"c.data_type, c.is_nullable "
                f"FROM information_schema.columns c "
                f"JOIN information_schema.tables t ON  "
                f"c.table_catalog = t.table_catalog "
                f"AND c.table_schema = t.table_schema "
                f"AND c.table_name = t.table_name "
                f"WHERE c.table_schema = '{schema_name}' "
                f"AND t.table_type = '{object_type}'")

    def get_dataset(self, schema_name: str, entry_type: EntryType):
        """Gets data for a table or a view."""
        # Dataset means that these entities can contain end user data.
        short_type = entry_type.name  # table or view, or the title of enum value
        if ( short_type == "TABLE" ):
            object_type = "BASE TABLE"
        else:
            object_type = "VIEW"
        query = self._get_columns(schema_name, object_type)
        return self._execute(query)
