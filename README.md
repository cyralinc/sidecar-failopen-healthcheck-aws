# Lambda Health-Checker

This is a lambda function that makes a health-check on a cyral sidecar that is connected to a `mysql` repository.
This lambda function needs access to CloudWatch, SecretsManager and to the sidecar in question, be it in a private or public
subnet.

## Building

To build the lambda image, run `make build`. It'll take the image name and tag from the `.env` file.
