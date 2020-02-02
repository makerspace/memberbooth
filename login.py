#!/usr/bin/env python3.7

import config
import argparse
from pathlib import Path
import subprocess
from src.util.logger import init_logger, get_logger
from src.backend.makeradmin import MakerAdminClient

init_logger()
logger = get_logger()

def ramdisk_is_mounted(directory):
    p = subprocess.run(f"df -T {directory}", stdout=subprocess.PIPE, shell=True, check=True, text=True)
    output = p.stdout.splitlines()
    return "tmpfs" in output[1]

def main():
    parser = argparse.ArgumentParser(description="Creates a login token on a RAM-disk for the memberbooth application")
    parser.add_argument("-u", "--maker-admin-base-url",
                        default='https://api.makerspace.se',
                        help="Base url of maker admin backend")
    parser.add_argument("-t", "--token", default="", help="Makeradmin token")
    ns = parser.parse_args()

    client = MakerAdminClient(ns.maker_admin_base_url, ns.token)
    while not client.is_logged_in():
        client.login()
    token = client.token
    logger.info(f"Logged in with token: {token}")

    token_dir = Path(config.token_path).parent
    if not token_dir.exists():
        token_dir.mkdir(exist_ok=True)
    if not ramdisk_is_mounted(token_dir):
        logger.info("Trying to mount RAM-disk")
        p = subprocess.run("sudo mount -t tmpfs -o \"size=1M\" none ramdisk/", shell=True, check=True)
        if not ramdisk_is_mounted(token_dir):
            raise TypeError(f"Failed to mount a RAM-disk to {token_dir}...")
    else:
        logger.info("RAM-disk is already mounted")

    with open(config.token_path, 'w') as f:
        f.write(token)

if __name__=="__main__":
    main()
