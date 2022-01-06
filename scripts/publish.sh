#!/bin/bash

bucket=${BUCKET:-cyral-public-assets-}
prefix=fail-open
version=${VERSION}


for region in $@
do
    if [[ ${APPEND_REGION} = "true" ]]; then
        _bucket=${bucket}${region}
    else
        _bucket=${bucket}
    fi
    echo "adding object to ${_bucket}/${prefix}/${version}/fail-open-lambda.zip"
    if [[ ${PUBLIC} = "true" ]]; then
        aws s3api put-object \
            --bucket ${bucket} \
            --key ${prefix}/${version}/fail-open-lambda.zip \
            --acl public-read \
            --body fail-open-lambda.zip  \
            --tagging "VERSION=${version}" \
            --metadata "VERSION=${version}"
    else
        aws s3api put-object \
            --bucket ${bucket} \
            --key ${prefix}/${version}/fail-open-lambda.zip \
            --body fail-open-lambda.zip  \
            --tagging "VERSION=${version}" \
            --metadata "VERSION=${version}"
    fi
done
