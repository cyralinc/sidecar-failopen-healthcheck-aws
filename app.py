"""
This function implements a health-check for a cyral sidecar connected to a mysql repo.
"""
import json
import logging
import os
from typing import Any, Dict, Tuple, Callable

import boto3
from botocore.exceptions import ClientError
from mysql import connector

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def observe(client, sidecar_address, metric: str, status: int) -> None:
    """
    Observe logs the status value on the metric
    """
    healthcheck_name = os.environ['CFSTACKNAME']
    return client.put_metric_data(
        Namespace='Route53PrivateHealthCheck',
        MetricData=[{
            'MetricName': f'{metric}: {healthcheck_name} ' +
            f'(Health Check for resource {sidecar_address})',
            'Dimensions': [{
                'Name': f'{metric} Health Check',
                'Value': f'{metric} Health Check'
            }],
            'Unit': 'None',
            'Value': status
        }, ])


def get_database_configuration(
    secret_name: str,
    session: boto3.Session,
    region_name: str
) -> Dict[str, Any]:
    """
        Gets the database configuration from secret manager on the secret_name location.
    """
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )

    except ClientError as err:
        # only handling resource not found. Other errors can be also handled.
        if err.response['Error']['Code'] == 'ResourceNotFoundException':
            logger.error(f"Secret not found on {secret_name}")
        raise err

    else:
        # right now, only json encoded string secrets are supported.
        if 'SecretString' in get_secret_value_response:
            secret = get_secret_value_response['SecretString']
            j = json.loads(secret)
            return j
        logger.error(
            f"Secret in wrong format found on {secret_name}")
        raise Exception(
            f"Secret in wrong format found on {secret_name}")


def try_connection(  # pylint: disable=too-many-arguments
    host: str,
    port: int,
    username: str,
    database: str,
    password: str,
    timeout: int = 2
):
    """
        Tries to establish a connection to a mysql repository with the given configurations.
    """
    try:
        logger.info(
            f"trying to establish mysql connection to {host}:{port}")
        cnx = connector.connect(
            connection_timeout=timeout,
            user=username,
            database=database,
            password=password,
            host=host,
            port=port
        )
        cursor = cnx.cursor()

        # sample query to just test dispatcher connectivity
        cursor.execute('SELECT 1;')
        cnx.close()
        logger.info(
            f'successful connection connecting to mysql on {host}:{port}')

    except connector.Error as err:
        logger.info(f'error connecting to mysql on {host}:{port}:', err)
        raise err


def lambda_handler(
    session: boto3.Session,
    sidecar_host: str,
    sidecar_port: int,
    number_of_retries: int
) -> Callable[[Any, Any], None]:
    """
        Creates a handler from the sidecar configuration and environment variables.
    """
    cloudwatch_client = session.client('cloudwatch')

    def handler(_, __):
        # retrieves the configuration for the db from secret manager
        db_info: Dict[str, Any] = get_database_configuration(
            os.environ["DBSECRET"],
            session,
            str(session.region_name)
        )

        db_info["host"] = os.environ["DBHOST"]
        db_info["port"] = os.environ["DBPORT"]
        db_info["database"] = os.environ["DBDATABASE"]

        # uses the same credentials but different address for sidecar connection
        sidecar_info = db_info.copy()
        sidecar_info["host"] = sidecar_host
        sidecar_info["port"] = sidecar_port

        for i in range(number_of_retries):
            logger.info(f"attempt {i+1} out of {number_of_retries}")

            # tries to connect. If successful, it's done, otherwise retry.
            status, done = full_connection(db_info, sidecar_info)
            if done:
                break

            logger.info("health check failed, retrying...")
            observe(cloudwatch_client, sidecar_host,
                    os.environ["SIDECARNAME"], status)
    return handler


def full_connection(
    db_info: Dict[str, Any],
    sidecar_info: Dict[str, Any]
) -> Tuple[bool, int]:
    """
        Full connection does the suite of connections, first trying to connect
        to the sidecar, and if failing, tries to connect to the databse directly.

        Logic is:
        - sidecar succeeds: return healthy and no need to retry
        - sidecar fails and db succeeds: return unhealthy and needs to retry
        - sidecar fails and db fails: return healthy and needs to retry
    """

    try:
        try_connection(**sidecar_info)

        # if the connection trought the sidecar succeeds, no need to retry, so we set
        # the metric as 1
        logger.info("connection succeeded, setting metric as healthy")
        return (True, 1)

    except connector.Error as err_sidecar:
        logger.info('Falling back to direct connection...')
        try:
            logger.info(err_sidecar)
            try_connection(**db_info)

            # if the connection to the sidecar fails and the connection to the db
            # succeeds, the sidecar is the problem, so set the metric as 0
            # and retry until reaches the limit.
            logger.info(
                f"DB alive but sidecar failing, setting metric as unhealthy. Error: {err_sidecar}")
            return (False, 0)
        except connector.Error as err_db:

            # if both sidecar and DB are failing, either the db is failing
            # or there is a connection issue. Either way, no need to trigger the
            # alarm
            logger.info(
                f"Sidecar and DB failing, setting metric as healthy. Error: {err_db}")
            return (False, 1)

    except:  # pylint: disable=bare-except
        logger.error(
            "An error occurred while performing the health check.")
        return (False, 1)


def entrypoint(event, context):
    """
    Entrypoint of the lambda function.
    """
    session = boto3.Session()

    sidecar_host = os.environ['SIDECARADDRESS']
    sidecar_port = int(os.environ['SIDECARPORT'])
    number_of_retries = int(os.environ['NRETRIES'])

    lambda_handler(
        session,
        sidecar_host,
        sidecar_port,
        number_of_retries
    )(event, context)
