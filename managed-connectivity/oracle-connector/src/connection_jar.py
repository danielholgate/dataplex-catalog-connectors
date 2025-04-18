"""jar file used for connecting to data source"""

# Jar file to connect to ORACLE
JAR_FILE = "ojdbc11.jar"

# Use the first SPARK_JAR_PATH below when the connector will be run in a container
# Use the second if you have downloaded the jar file to the oracle-connector directory to run locally

SPARK_JAR_PATH = f'/opt/spark/jars/{JAR_FILE}'
#SPARK_JAR_PATH = f'./{JAR_FILE}'