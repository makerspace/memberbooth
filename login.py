#!/usr/bin/env python3.7

import config
import argparse
from pathlib import Path
import subprocess
import os, stat
import pwd
import sys
from src.util.logger import init_logger, get_logger
import src.util.parser as parser_util
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
    boolean_login_action = parser_util.BooleanOptionalActionFactory("login", "skip")

    parser = argparse.ArgumentParser(description="Creates a login token on a RAM-disk for the memberbooth application")
    parser.add_argument("-U", "--memberbooth-username", default="memberbooth", help="Name of the user that will run the memberbooth")

    makeradmin_group = parser.add_argument_group("Makeradmin")
    makeradmin_group.add_argument("-u", "--maker-admin-base-url",
                        default=config.maker_admin_base_url,
                        help="Base url of maker admin backend")
    makeradmin_group.add_argument("--makeradmin", action=boolean_login_action, default=True, help="Whether to login Makeradmin or skip")

    slack_group = parser.add_argument_group("Slack")
    slack_group.add_argument("--slack", action=boolean_login_action, default=False, help="Whether to login Slack or skip")
    slack_group.add_argument("--slack-channel-id", help="Channel id for Slack channel")

    parser.add_argument("--ramdisk-path", default=config.ramdisk_path, help="Path to ramdisk")
    ns = parser.parse_args()

    memberbooth_username = ns.memberbooth_username
    try:
        pwnam = pwd.getpwnam(memberbooth_username)
    except KeyError:
        logger.error(f"User {memberbooth_username} does not exist")
        sys.exit(-1)

    token_dir = Path(ns.ramdisk_path)
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

    services = []
    if ns.makeradmin:
        services.append("makeradmin")
    if ns.slack:
        services.append("slack")

    for s in services:
        if s == "slack":
            token_path = os.path.join(ns.ramdisk_path, config.slack_token_filename)
            client = SlackClient(token_path=token_path, channel_id=ns.slack_channel_id)
        elif s == "makeradmin":
            token_path = os.path.join(ns.ramdisk_path, config.makeradmin_token_filename)
            client = MakerAdminClient(base_url=ns.maker_admin_base_url, token_path=token_path)

        try:
            while not client.configured:
                client.login()
        except EOFError:
            print()
            continue
        logger.info(f"Logged in with {s} token")

        logger.info(f"Creating token file '{token_path}'")
        with open(token_path, "w") as f:
            os.chmod(token_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP)
            os.chown(token_path, uid, gid)
            f.write(client.token)

    print("Done")

if __name__=="__main__":
    main()
