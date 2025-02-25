#!/bin/bash

IMAGE=dataplex-mysql-pyspark:0.0.2
PROJECT=daniel-dataplex
REGION=us-central1

REPO_IMAGE=${REGION}-docker.pkg.dev/${PROJECT}/docker-repo/dataplex-mysql-pyspark

docker build -t "${IMAGE}" .

# Tag and push to GCP container registry
gcloud config set project ${PROJECT}
gcloud auth configure-docker ${REGION}-docker.pkg.dev
docker tag "${IMAGE}" "${REPO_IMAGE}"
docker push "${REPO_IMAGE}"
