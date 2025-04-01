import enum

SOURCE_TYPE = "mysql"

# Expose to allow common code to load connector for MySQL
CONNECTOR_MODULE = "src.mysql_connector"
CONNECTOR_CLASS = "MysqlConnector"

# Enumeration representing the hierarchy in MySQL
class EntryType(enum.Enum):
    """Hierarchy of MySQL entries: Instance, database, table/view"""
    INSTANCE: str = "projects/{project}/locations/{location}/entryTypes/mysql-instance"
    DATABASE: str = "projects/{project}/locations/{location}/entryTypes/mysql-database"
    TABLE: str = "projects/{project}/locations/{location}/entryTypes/mysql-table"
    VIEW: str = "projects/{project}/locations/{location}/entryTypes/mysql-view"

# Number of hierarchy levels to write to output file before schema loop (2 = INSTANCE and DATABASE)
TOP_ENTRIES = 2

# Hierarchy level at which schema collection and database objects are gathered. Usually this is DATABASE
ENTRY_PROCESSING_LEVEL = EntryType.DATABASE

# List of MYSQL database object types to extract metadata for 
DB_OBJECTS_TO_PROCESS = [EntryType.TABLE, EntryType.VIEW]

def getOutputFileName(config):
    return f"{SOURCE_TYPE}-{config['host']}-{config['database']}.jsonl"

# Specific arguments for MySQL. Added to base common arguments
CONNECTOR_SPECIFIC_ARGS = [
["--host",str,True,"MySQL host server"],
["--port",int,True,"MySQL port number (usually 3306)"],
["--database",str,True,"Mysql database to connect to"],
["--user",str,True,"MySQL user"]
]