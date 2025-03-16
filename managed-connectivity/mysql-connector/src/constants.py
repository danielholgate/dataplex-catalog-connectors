import enum

SOURCE_TYPE = "mysql"

# Allows common library code to load the connector for MySQL
CONNECTOR_MODULE = "src.mysql_connector"
CONNECTOR_CLASS = "MysqlConnector"

class EntryType(enum.Enum):
    """Types of Mysql entries. Instance, database, table/view"""
    INSTANCE: str = "projects/{project}/locations/{location}/entryTypes/mysql-instance"
    DATABASE: str = "projects/{project}/locations/{location}/entryTypes/mysql-database"
    TABLE: str = "projects/{project}/locations/{location}/entryTypes/mysql-table"
    VIEW: str = "projects/{project}/locations/{location}/entryTypes/mysql-view"

# Number of hierarchy levels to write to output file before schema loop (2 = INSTANCE and DATABASE)
TOP_ENTRIES = 2

# List of database object types to be processed and metadata extracted for each schema
DB_OBJECTS_TO_PROCESS = [EntryType.TABLE, EntryType.VIEW]

def getOutputFileName(config):
    return f"{SOURCE_TYPE}-output-{config['database']}.jsonl"