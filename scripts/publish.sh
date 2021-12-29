#!/bin/bash

for region in $@
do
    aws s3api put-object \
        --bucket cyral-public-assets-$region \
        --key fail-open/fail-open-lambda-${TAG_NAME}.zip \
        --body fail-open-lambda.zip

    aws s3api put-object-acl \
        --bucket cyral-public-assets-$region \
        --key fail-open/fail-open-lambda-${TAG_NAME}.zip \
        --acl public-read
done
