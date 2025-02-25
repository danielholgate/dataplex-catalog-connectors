"""Reads Postgres using PySpark."""
from typing import Dict
from pyspark.sql import SparkSession, DataFrame

from src.constants import EntryType

SPARK_JAR_PATH = "/opt/spark/jars/postgresql-42.7.5.jar"
SPARK_JAR_PATH = "./postgresql-42.7.5.jar"

class PostgresConnector:
    """Reads data from Postgres and returns Spark Dataframes."""

    def __init__(self, config: Dict[str, str]):
        # PySpark entrypoint
        self._spark = SparkSession.builder.appName("PostgresIngestor") \
            .config("spark.jars", SPARK_JAR_PATH) \
            .getOrCreate()

        self._config = config
        self._url = f"jdbc:postgresql://{config['host']}:{config['port']}/{config['database']}"

    def _execute(self, query: str) -> DataFrame:
        """A generic method to execute any query."""
        return self._spark.read.format("jdbc") \
            .option("driver", "org.postgresql.Driver") \
            .option("url", self._url) \
            .option("query", query) \
            .option("user", self._config["user"]) \
            .option("password", self._config["password"]) \
            .load()

    def get_db_schemas(self) -> DataFrame:
        """In Postgres, schemas are schemas."""
        query = """
        SELECT DISTINCT schema_name 
        FROM information_schema.schemata
        WHERE schema_name NOT LIKE 'pg_%' 
        AND schema_name <> 'information_schema'
        """
        return self._execute(query)

    def _get_columns(self, schema_name: str, object_type: str) -> str:
        """Gets a list of columns in tables or views in a batch."""
        # Every line here is a column that belongs to the table or to the view.
        # This SQL gets data from ALL the tables in a given schema.
        return (f"SELECT c.table_name, c.column_name,  "
                f"c.data_type, c.is_nullable "
                f"FROM information_schema.columns c, "
                f"information_schema.tables t "
                f"WHERE c.table_schema = '{schema_name}' "
                f"AND t.table_name = c.table_name AND t.table_schema = c.table_schema "
                f"AND c.table_catalog = '{self._config['database']}' "
                f"AND t.table_type = '{object_type}'")

    def get_dataset(self, schema_name: str, entry_type: EntryType):
        """Gets data for a table or a view."""
        # Dataset means that these entities can contain end user data.
        if entry_type == EntryType.TABLE:
            object_type = 'BASE TABLE' 
        if entry_type == EntryType.VIEW:
            object_type = 'VIEW'
        query = self._get_columns(schema_name, object_type)
        return self._execute(query)
