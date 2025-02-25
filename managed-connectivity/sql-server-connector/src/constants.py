"""Constants that are used in the different files."""
import enum

SOURCE_TYPE = "sqlserver"

# Symbols for replacement
FORBIDDEN = "#"
ALLOWED = "!"


class EntryType(enum.Enum):
    """Types of SQL Server entries."""
    INSTANCE: str = "projects/{project}/locations/{location}/entryTypes/sqlserver-instance"
    DATABASE: str = "projects/{project}/locations/{location}/entryTypes/sqlserver-database"
    DB_SCHEMA: str = "projects/{project}/locations/{location}/entryTypes/sqlserver-schema"
    TABLE: str = "projects/{project}/locations/{location}/entryTypes/sqlserver-table"
    VIEW: str = "projects/{project}/locations/{location}/entryTypes/sqlserver-view"
