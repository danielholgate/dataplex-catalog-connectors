"""Reads SQL Server using PySpark."""
from typing import Dict
from pyspark.sql import SparkSession, DataFrame

from src.constants import EntryType

SPARK_JAR_PATH = "/opt/spark/jars/mssql-jdbc-9.4.1.jre8.jar"

class SQLServerConnector:
    """Reads data from SQL Server and returns Spark Dataframes."""

    def __init__(self, config: Dict[str, str]):
        # PySpark entrypoint
        self._spark = SparkSession.builder.appName("SQLServerIngestor") \
            .config("spark.jars", SPARK_JAR_PATH) \
            .getOrCreate()

        self._config = config

        if config['instancename'] and len(config['instancename']) > 0:
            self._url = f"jdbc:sqlserver://{config['host']}\{config['instancename']}:{config['port']}"
        else:
            self._url = f"jdbc:sqlserver://{config['host']}:{config['port']}"

    def _execute(self, query: str) -> DataFrame:
        """A generic method to execute any query."""
        return self._spark.read.format("jdbc") \
            .option("driver", "com.microsoft.sqlserver.jdbc.SQLServerDriver") \
            .option("url", self._url) \
            .option("query", query) \
            .option("user", self._config["user"]) \
            .option("password", self._config["password"]) \
            .option("trustServerCertificate","true") \
            .load()

    def get_db_schemas(self) -> DataFrame:
        """Gets a list of schemas in the database"""
        query = """
        SELECT s.name AS SCHEMA_NAME
        FROM sys.schemas s
        WHERE s.name NOT in ('db_accessadmin','db_backupoperator','db_datareader','db_datawriter','db_ddladmin','db_denydatareader','db_denydatawriter','db_owner','db_securityadmin','guest','sys','INFORMATION_SCHEMA')
        """
        return self._execute(query)

    def _get_columns(self, schema_name: str, object_type: str) -> str:
        """Gets a list of columns in tables or views."""
        # Every line here is a column that belongs to the table or to the view.
        # This SQL gets data from ALL the tables in a given schema.
        return (f"SELECT t.name AS TABLE_NAME, "
                f"c.name AS COLUMN_NAME, "
                f"ty.name AS DATA_TYPE, "
                f"c.is_nullable AS IS_NULLABLE "
                f"FROM sys.columns c "
                f"JOIN sys.tables t ON t.object_id = c.object_id "
                f"JOIN sys.types ty ON ty.user_type_id = c.system_type_id "
                f"JOIN sys.schemas s ON s.schema_id = t.schema_id "
                f"WHERE s.name = '{schema_name}' "
                f"AND t.type = '{object_type}'")

    def get_dataset(self, schema_name: str, entry_type: EntryType):
        """Gets data for a table or a view."""
        # Dataset means that these entities can contain end user data.
        short_type = {"TABLE":"U", "VIEW":"V"}
        query = self._get_columns(schema_name, short_type[entry_type.name])
        return self._execute(query)
