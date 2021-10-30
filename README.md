# AWS Health Check for Cyral Sidecars

## Introduction

This repository contains a lambda function that is part of the sidecar fail open feature.
Refer to the [sidecar fail open deployment template](https://github.com/cyralinc/cloudformation-sidecar-failopen)
for more information and overall architectural guidelines.

The lambda function contained here offers health check verification for `MySQL` databases that are bound to
Cyral Sidecars.

## Limitations

See all the fail open feature limitations [here](https://github.com/cyralinc/cloudformation-sidecar-failopen#Limitations).

## Build

This lambda is packaged as a Docker image and is publicly available at `gcr.io/cyralpublic/health-check-aws:<version>`
where `<version>` is the version tag as seen in this repository.

In order to **build and publish** this lambda to a different repository, edit the `.env` file informing the desired
image and tag and then run `make build`.

## Execution Requirements

In order to properly execute, the lambda needs IAM permissions to access AWS CloudWatch and AWS SecretsManager.
It also needs networking access to the target sidecar, target repository and also to AWS CloudWatch and
AWS SecretsManager.

The detailed IAM permissions required by the execution role are the following:

- AWS SecretsManager: required to access the database credentials
  - `secretsmanager:GetSecretValue`
- AWS EC2: required to create the network interface so the lambda can access the VPC
  - `ec2:CreateNetworkInterface`
  - `ec2:DescribeNetworkInterfaces`
  - `ec2:DeleteNetworkInterface`
- AWS CloudWatch: required to log events and write the health check metrics
  - `logs:PutLogEvents`
  - `logs:CreateLogStream`
  - `logs:CreateLogGroup`
  - `logs:DescribeLogStreams`
  - `cloudwatch:PutMetricData`

The necessary permissions can be described as follows in CloudFormation:
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
