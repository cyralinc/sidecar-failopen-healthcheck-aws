#!/bin/bash

for region in $@
do
    echo "adding object to cyral-public-assets-$region/${BUCKET_KEY_PREFIX}/fail-open-lambda-${VERSION}.zip"
    aws s3api put-object \
        --bucket cyral-public-assets-$region \
        --key ${BUCKET_KEY_PREFIX}/fail-open-lambda-${VERSION}.zip \
        --body fail-open-lambda.zip

    echo "publishing object to cyral-public-assets-$region/${BUCKET_KEY_PREFIX}/fail-open-lambda-${VERSION}.zip"
    aws s3api put-object-acl \
        --bucket cyral-public-assets-$region \
        --key ${BUCKET_KEY_PREFIX}/fail-open-lambda-${VERSION}.zip \
        --acl public-read
done
