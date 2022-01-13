"""
This function implements a health-check for a cyral sidecar connected to a mysql repo.
"""
import json
import logging
import os
from typing import Any, Dict, Tuple, Callable

from botocore.exceptions import ClientError
from botocore.session import Session
from botocore.config import Config
import mysql.connector as mysql
import psycopg2

logger = logging.getLogger()



def get_log_level() -> int:
    LOG_LEVEL = os.environ["FAIL_OPEN_LOG_LEVEL"]
    if LOG_LEVEL == "DEBUG":
        return logging.DEBUG
    if LOG_LEVEL == "INFO":
        return logging.INFO
    if LOG_LEVEL == "WARNING":
        return logging.WARNING
    if LOG_LEVEL == "ERROR":
        return logging.ERROR
    if LOG_LEVEL == "FATAL":
        return logging.FATAL
    return logging.WARNING

level = get_log_level()
# setting log levels for boto
logging.getLogger('boto3').setLevel(level)
logging.getLogger('botocore').setLevel(level)
logging.getLogger('nose').setLevel(level)

logger.setLevel(level)

def observe(client, sidecar_host, metric: str, status: int) -> None:
    """
    Observe logs the status value on the metric
    """
    healthcheck_name = os.environ['FAIL_OPEN_CF_STACK_NAME']
    return client.put_metric_data(
        Namespace='Route53PrivateHealthCheck',
        MetricData=[{
            'MetricName': f'{metric}: {healthcheck_name} ' +
            f'(Health Check for resource {sidecar_host})',
            'Dimensions': [{
                'Name': f'{metric} Health Check',
                'Value': f'{metric} Health Check'
            }],
            'Unit': 'None',
            'Value': status
        }, ])


def get_database_configuration(
    secret_name: str,
    session: Session,
    region_name: str
) -> Dict[str, Any]:
    """
        Gets the database configuration from secret manager on the secret_name location.
    """
    client = session.create_client(
        service_name='secretsmanager',
        region_name=region_name,
        config=Config(
            connect_timeout=5,
            read_timeout=60,
            retries={'max_attempts': 2}
        )
    )

    try:
        logger.info(
            f"Trying to reach secrets manager for DB credentials. Secret location: {secret_name}"
        )
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

            return {"username": j["username"], "password": j["password"]}
        logger.error(
            f"Secret in wrong format found on {secret_name}")
        raise Exception(
            f"Secret in wrong format found on {secret_name}")



def mysql_connect(*args):
    cnx = mysql.connect(*args)
    return cnx

def pg_connect(host, port, username, database, password, *_):
    cnx = psycopg2.connect(
            dbname=database,
            user=username,
            password=password,
            host=host,
            port=port
    )
    return cnx

repo_connectors = {
        "mysql": mysql_connect,
        "postgresql": pg_connect,
    }

def try_connection(  # pylint: disable=too-many-arguments
    repo_type: str,
    host: str,
    port: int,
    username: str,
    database: str,
    password: str,
    connection_timeout: int = 2
):
    """
        Tries to establish a connection to a mysql repository with the given configurations.
    """
    try:
        logger.info(
            f"trying to establish {repo_type} connection to {host}:{port}")
        cnx = repo_connectors[repo_type](host, port, username, database, password, connection_timeout)
        cursor = cnx.cursor()

        # sample query to just test dispatcher connectivity
        cursor.execute('SELECT 1;')
        cnx.close()
        logger.info(
            f'successful connection connecting to mysql on {host}:{port}')

    except mysql.Error as err:
        logger.info(f'error connecting to {repo_type} on {host}:{port}: {err}')
        raise err


def lambda_handler(
    session: Session,
    sidecar_host: str,
    sidecar_port: int,
    number_of_retries: int
) -> Callable[[Any, Any], None]:
    """
        Creates a handler from the sidecar configuration and environment variables.
    """

    cloudwatch_client = session.create_client('cloudwatch', config=Config(
        connect_timeout=5, read_timeout=60, retries={'max_attempts': 2}))

    def handler(_, __):
        # retrieves the configuration for the db from secret manager
        db_info: Dict[str, Any] = get_database_configuration(
            os.environ["FAIL_OPEN_REPO_SECRET"],
            session,
            os.environ['AWS_REGION']
        )

        db_info["host"] = os.environ["FAIL_OPEN_REPO_HOST"]
        db_info["port"] = os.environ["FAIL_OPEN_REPO_PORT"]
        db_info["repo_type"] = os.environ["FAIL_OPEN_REPO_TYPE"]
        db_info["database"] = os.environ["FAIL_OPEN_REPO_DATABASE"]

        # uses the same credentials but different address for sidecar connection
        sidecar_info = db_info.copy()
        sidecar_info["host"] = sidecar_host
        sidecar_info["port"] = sidecar_port
        status = 0

        if number_of_retries < 0:
            raise Exception("number of retries must be bigger than 0")
        for i in range(number_of_retries + 1):
            logger.info(f"attempt {i+1} out of {number_of_retries + 1}")

            # tries to connect. If successful, it's done, otherwise retry.
            done, status = full_connection(db_info, sidecar_info)
            if done:
                break

            logger.info("health check failed, retrying...")
        observe(cloudwatch_client, sidecar_host,
                os.environ["FAIL_OPEN_SIDECAR_NAME"], status)
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

    except mysql.Error as err_sidecar:
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
        except mysql.Error as err_db:

            # if both sidecar and DB are failing, either the db is failing
            # or there is a connection issue. Either way, no need to trigger the
            # alarm
            logger.info(
                f"Sidecar and DB failing, setting metric as healthy. Error: {err_db}")
            return (False, 1)


def entrypoint(event, context):
    """
    Entrypoint of the lambda function.
    """
    session = Session()

    sidecar_host = os.environ['FAIL_OPEN_SIDECAR_HOST']
    sidecar_port = int(os.environ['FAIL_OPEN_SIDECAR_PORT'])
    number_of_retries = int(os.environ['FAIL_OPEN_N_RETRIES'])

    lambda_handler(
        session,
        sidecar_host,
        sidecar_port,
        number_of_retries
    )(event, context)
