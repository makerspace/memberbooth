#!/usr/bin/env python3.7

import config
import argparse
from pathlib import Path
import subprocess
import os, stat
import pwd
import sys
from src.util.logger import init_logger, get_logger
from src.backend.makeradmin import MakerAdminClient

init_logger("login")
logger = get_logger()
start_command = " ".join(sys.argv)

def ramdisk_is_mounted(directory):
    p = subprocess.run(f"df -T {directory}", stdout=subprocess.PIPE, shell=True, check=True, text=True)
    output = p.stdout.splitlines()
    return "tmpfs" in output[1]

def main():
    logger.info(f"Starting {sys.argv[0]} as \n\t{start_command}")

    parser = argparse.ArgumentParser(description="Creates a login token on a RAM-disk for the memberbooth application")
    parser.add_argument("-U", "--memberbooth-username", default="memberbooth", help="Name of the user that will run the memberbooth")
    parser.add_argument("-u", "--maker-admin-base-url",
                        default=config.maker_admin_base_url,
                        help="Base url of maker admin backend")
    parser.add_argument("--makeradmin-token-path", "-t", help="Path to Makeradmin token", default=config.makeradmin_token_path)
    ns = parser.parse_args()

    memberbooth_username = ns.memberbooth_username
    try:
        pwnam = pwd.getpwnam(memberbooth_username)
    except KeyError:
        logger.error(f"User {memberbooth_username} does not exist")
        sys.exit(-1)

    token = ""
    if Path(ns.makeradmin_token_path).is_file():
        with open(ns.makeradmin_token_path) as f:
            token = f.read()

    client = MakerAdminClient(ns.maker_admin_base_url, ns.makeradmin_token_path, token)
    while not client.is_logged_in():
        try:
            client.login()
        except EOFError:
            print()
            sys.exit(0)
    token = client.token
    logger.info(f"Logged in with token")

    token_dir = Path(config.makeradmin_token_path).parent
    token_dir.mkdir(exist_ok=True)
    if ramdisk_is_mounted(token_dir):
        logger.warning("RAM-disk is already mounted. Unmounting.")
        subprocess.run(f"sudo umount {token_dir}", check=True, shell=True)

    logger.info("Trying to mount RAM-disk to {token_dir}")
    uid = pwd.getpwuid(os.getuid()).pw_uid
    gid = pwnam.pw_gid
    p = subprocess.run(f"sudo mount -t tmpfs -o \"size=1M,mode=750,uid={uid},gid={gid}\" none {token_dir}", shell=True, check=True)
    if not ramdisk_is_mounted(token_dir):
        raise TypeError(f"Failed to mount a RAM-disk to {token_dir}...")

    logger.info(f"Creating token file '{config.makeradmin_token_path}'")
    with open(config.makeradmin_token_path, "w") as f:
        os.chmod(config.makeradmin_token_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP)
        os.chown(config.makeradmin_token_path, uid, gid)
        f.write(token)

    print("Login successful")

if __name__=="__main__":
    main()
