from typing import Dict
from src.constants import EntryType
from pyspark.sql import DataFrame
from abc import ABC, abstractmethod

# Interface defines methos to pass metadata to common files
class ExternalSourceConnector(ABC):

    @abstractmethod
    def get_dataset(self, schema_name: str, entry_type: EntryType):
        """Returns dataframe of schemas to extract objects from"""
        pass

    @abstractmethod
    def get_db_schemas(self) -> DataFrame:
        """Returns dataframe of schemas to extract objects from"""
        pass