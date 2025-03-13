"""jar file used for connecting to data source"""

# Jar file to connect to SQL SERVER
JAR_FILE = "mssql-jdbc-12.8.1.jre11.jar"

# Use the first SPARK_JAR_PATH below for Pyspark when the connector will be run in a container
# Use the second if you have downloaded the jar file to the sqlserver-connector directory to run locally

#SPARK_JAR_PATH = f'/opt/spark/jars/{JAR_FILE}'
SPARK_JAR_PATH = f'./{JAR_FILE}'