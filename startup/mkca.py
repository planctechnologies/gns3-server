# -*- coding: utf-8 -*-
"""
Utility code to perform CA generation and signing
"""
import os
import subprocess


def setup(root="demoCA"):
    """
    Create filesystem structure to host certificates and keys
    """
    dirs = (
        os.path.join(root, 'private'),
        os.path.join(root, 'certs'),
        os.path.join(root, 'crl'),
        os.path.join(root, 'newcerts'),
    )
    for d in dirs:
        try:
            os.makedirs(d, 0o700)
        except FileExistsError:
            continue

    # Serial and registry
    with open(os.path.join(root, 'serial'), 'w+') as f:
        f.write("011E")
    open(os.path.join(root, 'index.txt'), 'a').close()


def gen_cacert(root, countryName, stateOrProvinceName, locality, organizationName, commonName):
    """
    Generate the ca cert, cacert.pem should be sent to the client
    """
    subj = '/C={}/ST={}/L={}/O={}/CN={}'.format(
        countryName, stateOrProvinceName, locality, organizationName, commonName
    )
    ca_key_path = os.path.join(root, 'private', 'cakey.pem')
    args = (
        'openssl',
        'req',
        '-new',
        '-newkey',
        'rsa:4096',
        '-days', '365',
        '-nodes',
        '-x509',
        '-subj', subj,
        '-keyout', ca_key_path,
        '-out', os.path.join(root, 'cacert.pem'),
    )
    # if private key already exists, make it writeable for a while
    try:
        os.chmod(ca_key_path, 0o600)
    except FileNotFoundError:
        pass
    subprocess.check_call(args)
    # finally set the right permissions on private key
    os.chmod(ca_key_path, 0o400)


def verify_cacert(cacert):
    """
    Verify purpose of a CA
    """
    args = (
        'openssl',
        'x509',
        '-purpose',
        '-in', cacert,
        '-inform', 'PEM'
    )
    subprocess.check_call(args)


def gen_servercert(countryName, stateOrProvinceName, locality, organizationName, commonName):
    """
    Configure server certificate, server.csr should be sent to the CA
    """
    args = (
        'openssl',
        'genrsa',
        '-out', 'server.key',
        '4096',
    )
    subprocess.check_call(args)

    subj = '/C={}/ST={}/L={}/O={}/CN={}'.format(
        countryName, stateOrProvinceName, locality, organizationName, commonName
    )
    args = (
        'openssl',
        'req',
        '-new',
        '-newkey', 'rsa:4096',
        '-key', 'server.key',
        '-out', 'server.csr',
        '-subj', subj,
    )
    subprocess.check_call(args)


def sign():
    """
    Sign the certificate
    """
    args = (
        'openssl',
        'ca',
        '-in', 'server.csr',
        '-out', 'server.pem',
        '-batch',
        '-passin', 'pass:keypass',
    )
    subprocess.check_call(args)


if __name__ == '__main__':
    """
    Example usage
    """
    setup("demoCA")
    gen_cacert("demoCA", "CA", "Canada", "Canada", "GNS3", "CA")
    verify_cacert("demoCA/cacert.pem")
    gen_servercert("CA", "Canada", "Canada", "GNS3", "CA")
    sign()
