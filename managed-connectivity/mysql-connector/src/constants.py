"""Constants for MySQL"""
import enum

SOURCE_TYPE = "mysql"

# Symbols for replacement
FORBIDDEN = "#"
ALLOWED = "!"

# Allows common library code to load the specific connector for MySQL
CONNECTOR_MODULE = "src.mysql_connector"
CONNECTOR_CLASS = "MysqlConnector"

class EntryType(enum.Enum):
    """Types of Mysql entries. Instance, database, table/view"""
    INSTANCE: str = "projects/{project}/locations/{location}/entryTypes/mysql-instance"
    DATABASE: str = "projects/{project}/locations/{location}/entryTypes/mysql-database"
    TABLE: str = "projects/{project}/locations/{location}/entryTypes/mysql-table"
    VIEW: str = "projects/{project}/locations/{location}/entryTypes/mysql-view"
