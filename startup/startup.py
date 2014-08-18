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
import os
import uuid
import subprocess
import logging
log = logging.getLogger(__name__)

import click

# following 3 lines are a workaround to let this script be run both directly with
# `python startup.py` and from the `gns3startup` entrypoint installed with setuptools
here = os.path.realpath(os.path.dirname(__file__))
sys.path.append(os.path.normpath(here))
from core import mkca


def validate_environment():
    """
    Ensure gns3-server and gns3-dms are available on the system
    """
    try:
        from gns3server import version
    except ImportError:
        click.echo('GNS3 server not found!')
        return False

    try:
        from gns3dms import version
    except ImportError:
        click.echo('GNS3 dead man switch not found!')
        return False

    return True


def create_ssl_certificate(ca_root, dry=False):
    """
    Creates an SSL certificate, residing where Tornado libraries will find it.

    We first create a custom CA to sign the certificate; then we create the server certificate.

    :return: the paths to the files containing the CA and the server certificate
    """
    if dry:
        return "/tmp", "/tmp"

    mkca.setup(ca_root)
    ca_cert = mkca.gen_cacert(ca_root, "CA", "Canada", "Canada", "GNS3", "CA")
    mkca.gen_servercert(ca_root, "CA", "Canada", "Canada", "GNS3", "CA")
    server_cert = mkca.sign(ca_root)
    return ca_cert, server_cert


def get_random_string():
    """
    Create a password for clients to use when connecting to servers, a simple approach
    is to use Python's UUID

    :return: a 32 bytes random string
    """
    return uuid.uuid4().hex


def launch_dms(user_id, api_key, instance_id, region, deadtime, dry=False):
    """
    Launch dead man switch scripts

    :return: True if process started successfully, False otherwise
    """
    dms_exe = "gns3dms"
    try:
        file = '/etc/hosts'  # FIXME with the name of the file touched by gns3 server
        args = [
            dms_exe,
            "--cloud_user_name", user_id,
            "--cloud_api_key", api_key,
            "--instance_i", instance_id,
            "--region", region,
            "--deadtime", deadtime,
            "--file", file,
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


def launch_gns3_server(dry=False):
    """
    Launch GNS3 server process

    :return: True if process started successfully, False otherwise
    """
    server_exe = "gns3server"
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
@click.option('--dry', default=False,
              help="Don't actually do anything")
@click.option('--debug', default=False,
              help='Print debug messages on stdout')
def start(instance_id, user_id, api_key, region, deadtime, dry, debug):
    """
    Script entry point
    """
    # check everything we need is installed
    if not validate_environment():
        return 1

    # launch the dead man switch
    if not launch_dms(user_id, api_key, instance_id, region, deadtime, dry):
        return 2

    # launch gns3 server
    if not launch_gns3_server(dry):
        return 3

    # all good, generate cert and password and print them on the standard output
    password = get_random_string()
    ca_root_path = "GNS3CA"  # path in the CWD
    ca_cert_path, server_cert_path = create_ssl_certificate(ca_root_path, dry)

    click.echo("{} {}".format(password, ca_cert_path))
    return 0


def main():
    sys.exit(start(auto_envvar_prefix='GNS3START'))


if __name__ == '__main__':
    main()
