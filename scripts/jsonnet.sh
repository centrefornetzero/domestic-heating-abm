#!/bin/bash

jsonnet -y --ext-str PROJECT_ID \
    --ext-str IMAGE_URI \
    --ext-str SHORT_SHA \
    --ext-str BUCKET_NAME k8s/job.jsonnet
