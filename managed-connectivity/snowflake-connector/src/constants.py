"""Constants that are used in the different files."""
import enum

SOURCE_TYPE = "snowflake"

# Symbols for replacement
FORBIDDEN = "#"
ALLOWED = "!"

class EntryType(enum.Enum):
    """Types of Snowflake entries."""
    ACCOUNT: str = "projects/{project}/locations/{location}/entryTypes/snowflake-account"
    DATABASE: str = "projects/{project}/locations/{location}/entryTypes/snowflake-database"
    DB_SCHEMA: str = "projects/{project}/locations/{location}/entryTypes/snowflake-schema"
    TABLE: str = "projects/{project}/locations/{location}/entryTypes/snowflake-table"
    VIEW: str = "projects/{project}/locations/{location}/entryTypes/snowflake-view"
