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
import subprocess
import os
import logging
log = logging.getLogger(__name__)

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


def create_ssl_certificate(dry=False):
    """
    Creates an SSL certificate, residing where Tornado libraries will find it.

    :return: the path to the file containing the certificate
    """
    # TODO
    if dry:
        return "/tmp"
    return ""


def get_random_string():
    """
    Create a password for clients to use when connecting to servers, a simple approach
    is to use Python's UUID

    :return: a 32 bytes random string
    """
    return uuid.uuid4().hex


def launch_dms(gns3_dms_path, user_id, api_key, instance_id, region, deadtime, dry=False):
    """
    Launch dead man switch scripts

    :return: True if process started successfully, False otherwise
    """
    dms_exe = os.path.join(gns3_dms_path, "gns3dms", "main.py")
    try:
        file = '/etc/hosts'  # FIXME with the name of the file touched by gns3 server
        args = [
            dms_exe,
            "--cloud_user_name {}".format(user_id),
            "--cloud_api_key {}".format(api_key),
            "--instance_id {}".format(instance_id),
            "--region {}".format(region),
            "--deadtime {}".format(deadtime),
            "--file {}".format(file),
            "-k",
            "--background"
        ]
        log.debug("Launching dms with args: {}".format(args))

        if not dry:
            subprocess.check_call(args)
    except subprocess.CalledProcessError as e:
        click.echo("Error launching GNS3 dead man switch: {}".format(e))
        return False
    return True


def launch_gns3_server(gns3_server_path, dry=False):
    """
    Launch GNS3 server process

    :return: True if process started successfully, False otherwise
    """
    server_exe = os.path.join(gns3_server_path, "gns3server", "main.py")
    try:
        args = [
            server_exe
        ]
        log.debug("Launching GNS3 server with args: {}".format(args))

        if not dry:
            subprocess.check_call(args)
    except subprocess.CalledProcessError as e:
        click.echo("Error launching GNS3 server: {}".format(e))
        return False
    return True


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
@click.option('--debug', default=False,
              help='Print debug messages on stdout')
def start(instance_id, user_id, api_key, region, deadtime, gns3_server_path, gns3_dms_path, dry):
    """
    Script entry point
    """
    # check everything we need is installed
    if not validate_environment(gns3_server_path, gns3_dms_path):
        return 1

    # launch the dead man switch
    if not launch_dms(gns3_dms_path, user_id, api_key, instance_id, region, deadtime, dry):
        return 2

    # launch gns3 server
    if not launch_gns3_server(gns3_server_path, dry):
        return 3

    # all good, generate cert and password and print them on the standard output
    password = get_random_string()
    cert_path = create_ssl_certificate(dry)

    click.echo("{} {}".format(password, cert_path))
    return 0


if __name__ == '__main__':
    sys.exit(start(auto_envvar_prefix='GNS3START'))