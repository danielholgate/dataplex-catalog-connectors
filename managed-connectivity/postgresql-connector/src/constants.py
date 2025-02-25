"""Constants that are used in the different files."""
import enum

SOURCE_TYPE = "postgresql"

# Symbols for replacement
FORBIDDEN = "#"
ALLOWED = "!"


class EntryType(enum.Enum):
    """Types of Postgres entries."""
    INSTANCE: str = "projects/{project}/locations/{location}/entryTypes/postgresql-instance"
    DATABASE: str = "projects/{project}/locations/{location}/entryTypes/postgresql-database"
    DB_SCHEMA: str = "projects/{project}/locations/{location}/entryTypes/postgresql-schema"
    TABLE: str = "projects/{project}/locations/{location}/entryTypes/postgresql-table"
    VIEW: str = "projects/{project}/locations/{location}/entryTypes/postgresql-view"
