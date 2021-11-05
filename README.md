# AWS Health Check for Cyral Sidecars

## Introduction

This repository contains a lambda function that is part of the sidecar fail open feature.
Refer to the [sidecar fail open deployment template](https://github.com/cyralinc/cloudformation-sidecar-failopen)
for more information and overall architectural guidelines.

The lambda function contained here offers health check verification for `MySQL` databases that are bound to
Cyral Sidecars.

## Limitations

See all the fail open feature limitations [here](https://github.com/cyralinc/cloudformation-sidecar-failopen#limitations).

## Build

This lambda is packaged as a Docker image and must be published to the AWS account and region where
the lambda will be deployed. The next steps will guide you through the publishing process:

1. Create a repository named `sidecar-failopen-healthcheck-aws` on the target accound and region in
AWS ECR.

2. Export environment variables `AWS_REGION` and `AWS_ACCOUNT` with the target region and account:

```bash
# Example
export AWS_REGION=us-east-1
export AWS_ACCOUNT=0123456789
```

3. Log in to ECR at the command line:

```bash
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com
```

4. Build and publish the lambda:

```bash
make
```

## Execution Requirements

In order to properly execute, the lambda needs IAM permissions to access AWS CloudWatch and AWS Secrets Manager.
It also needs network access to the target sidecar, target repository, and also to AWS CloudWatch and
AWS Secrets Manager.

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
