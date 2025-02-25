"""Constants that are used in the different files."""
import enum

SOURCE_TYPE = "mysql"

# Symbols for replacement
FORBIDDEN = "#"
ALLOWED = "!"


class EntryType(enum.Enum):
    """Types of Mysql entries. Instance, database, table/view"""
    INSTANCE: str = "projects/{project}/locations/{location}/entryTypes/mysql-instance"
    DATABASE: str = "projects/{project}/locations/{location}/entryTypes/mysql-database"
    TABLE: str = "projects/{project}/locations/{location}/entryTypes/mysql-table"
    VIEW: str = "projects/{project}/locations/{location}/entryTypes/mysql-view"
