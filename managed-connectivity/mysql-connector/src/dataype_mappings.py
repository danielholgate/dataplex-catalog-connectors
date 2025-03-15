# Provides mapping between MySQL data types and Dataplex Catalog
def metadata_type_converter(data_type: str):
    """Returns Dataplex metadata type which maps to Mysql native type."""
    if data_type.startswith("int") or data_type.startswith("tinyint") or data_type.startswith("smallint") or data_type.startswith("mediumint") or data_type.startswith("bigint") or data_type.startswith("decimal") or data_type.startswith("numeric") or data_type.startswith("float") or  data_type.startswith("double") :
        return "NUMBER"
    if data_type.startswith("varchar") or data_type.startswith("char") or data_type.startswith("text") or data_type.startswith("tinytext") or data_type.startswith("mediumtext") or data_type.startswith("longtext"):
        return "STRING"
    if data_type.startswith("binary") or data_type.startswith("varbinary") or data_type.startswith("blob") or data_type.startswith("tinyblob") or data_type.startswith("mediumblob") or data_type.startswith("longblob"):
        return "BYTES"
    if data_type.startswith("timestamp") or data_type.startswith("datetime"):
        return "TIMESTAMP"
    if data_type.startswith("date"):
        return "DATETIME"
    return "OTHER"

# builds the name for the Datplaex entry
def build_name(data_type: str):
    if entry_type == EntryType.DATABASE:
        instance = create_name(config, EntryType.INSTANCE)
    if entry_type == EntryType.TABLE:
        db_schema = create_name(config, EntryType.DATABASE, schema_name)
        return f"{db_schema}/tables/{table_name}"
    if entry_type == EntryType.VIEW:
        db_schema = create_name(config, EntryType.DATABASE, schema_name)
        return f"{db_schema}/views/{table_name}"