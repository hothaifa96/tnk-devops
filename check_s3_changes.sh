#!/bin/bash

# Define variables
BUCKET_NAME="thinking-bucket"
REGION="eu-west-1"

# Get the current time and time one hour ago in ISO 8601 format
CURRENT_TIME=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
ONE_HOUR_AGO=$(date -u -d '-1 hour' +"%Y-%m-%dT%H:%M:%SZ")

# List objects in the S3 bucket and check their LastModified times
CHANGED_FILES=$(aws s3api list-objects-v2 \
    --bucket "$BUCKET_NAME" \
    --query "Contents[?LastModified>=\`$ONE_HOUR_AGO\`].{Key: Key, LastModified: LastModified}" \
    --region "$REGION" \
    --output json)

# Check if any files were changed
if [[ $CHANGED_FILES == "[]" ]]; then
    echo "No files have been modified in the last hour."
    # exit 1

else
    echo "Files modified in the last hour:"
    echo "$CHANGED_FILES" | jq -r '.[] | "\(.Key) - LastModified: \(.LastModified)"'
    exit 0

fi