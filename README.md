# Lambda Health-Checker

This is a lambda function that makes a health-check on a cyral sidecar that is connected to a `mysql` repository.
This lambda function needs access to CloudWatch, SecretsManager and to the sidecar in question, be it in a private or public
subnet.

## Building

To build the lambda image, run `make build`. It'll take the image name and tag from the `.env` file.

## Permissions
The permissions required for the execution role are the following:

- secretsmanager:GetSecretValue
  - for accessing the credentials for the database
- ec2:CreateNetworkInterface
- ec2:DescribeNetworkInterfaces
- ec2:DeleteNetworkInterface
  - for creating and interface on the VPC and getting access to the sidecar
- logs:PutLogEvents
- logs:CreateLogStream
- logs:CreateLogGroup
- logs:DescribeLogStreams
  - for observability
- cloudwatch:PutMetricData
  - for writing to the metric that will be the healthcheck

On cloudformation, this is the general format of the permissions:
```yaml
- Effect: Allow
  Action:
    - "secretsmanager:GetSecretValue"
  Resource:
    - !Sub 'arn:aws:secretsmanager:${AWS::Region}:${AWS::AccountId}:secret:${DBSecretLocation}*'

- Effect: Allow
  Action:
    - ec2:CreateNetworkInterface
    - ec2:DescribeNetworkInterfaces
    - ec2:DeleteNetworkInterface
  Resource: '*'

- Effect: Allow
  Action:
    - logs:PutLogEvents
    - logs:CreateLogStream
    - logs:CreateLogGroup
    - logs:DescribeLogStreams
  Resource:
    - !Sub 'arn:aws:logs:${AWS::Region}:${AWS::AccountId}:*'

- Effect: Allow
  Action:
    - cloudwatch:PutMetricData
  Resource: '*'
 
```
