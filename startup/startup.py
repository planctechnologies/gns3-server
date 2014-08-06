# -*- coding: utf-8 -*-
"""
Once the server instance is running, the GUI ssh'es in and runs this script to set up and laung
the server.

Following data MUST be passed in to the script as command line parameters or environment variables:
    instance id: --instance-id or GNS3START_INSTANCE_ID env var
    rackspace user id: --user-id or GNS3START_USER_ID env var
    rackspace api key: --api-key or GNS3START_API_KEY env var
    rackspace region: --region or GNS3START_REGION env var
    dead time in seconds: --deadtime or GNS3START_DEADTIME env var

The server script then proceeds to:
    create an SSL certificate, residing where Tornado libraries will find it.
    create a password that Tornado can use to authenticate the client.
    create a config file for the GNS3 server process.
    spawn the GNS3 server process in the background.
    spawn the GNS3 deadman timer using the 5 bits of information passed in.
"""
import sys
import uuid

import click


def validate_environment(gns3_server_path, gns3_dms_path):
    """
    Ensure gns3-server and gns3-dms are available on the system
    """
    sys.path.append(gns3_server_path)
    try:
        from gns3server import version
    except ImportError:
        click.echo('GNS3 server not found at: {}'.format(gns3_server_path))
        return False

    sys.path.append(gns3_dms_path)
    try:
        from gns3dms import version
    except ImportError:
        click.echo('GNS3 dead man switch not found at: {}'.format(gns3_dms_path))
        return False

    return True


def create_ssl_certificate():
    """
    Creates an SSL certificate, residing where Tornado libraries will find it.
    """
    pass


def get_random_string():
    """
    Create a password for clients to use when connecting to servers, a simple approach
    is to use Python's UUID returning a 32 bytes random string
    """
    return uuid.uuid4().hex


@click.command()
@click.option('--instance-id', required=True, envvar='INSTANCE_ID',
              help='Rackspace identifier of the running instance')
@click.option('--user-id', required=True, envvar='USER_ID',
              help='Rackspace user id')
@click.option('--api-key', required=True, envvar='API_KEY',
              help='Rackspace api key')
@click.option('--region', required=True, envvar='REGION',
              help='Rackspace region of the running instance')
@click.option('--deadtime', required=True, envvar='DEADTIME',
              help='Timeout value in seconds after which the running instance is terminated')
@click.option('--gns3-server-path', envvar='GNS3_SERVER_PATH', default='.',
              help='Path to gns3-server installation')
@click.option('--gns3-dms-path', envvar='GNS3_DMS_PATH', default='.',
              help='Path to dead man switch installation')
@click.option('--dry', default=False,
              help="Don't actually do anything")
def start(instance_id, user_id, api_key, region, deadtime, gns3_server_path, gns3_dms_path, dry):
    """
    Script entry point
    """
    if not validate_environment(gns3_server_path, gns3_dms_path):
        sys.exit(1)

    print(instance_id)


if __name__ == '__main__':
    start(auto_envvar_prefix='GNS3START')