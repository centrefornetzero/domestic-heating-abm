#!/bin/bash

jsonnet --ext-str PROJECT_ID \
    --ext-str IMAGE_URI \
    --ext-str JOB_NAME \
    --ext-str BUCKET_NAME k8s/job.jsonnet
