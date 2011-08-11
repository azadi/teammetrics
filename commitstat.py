#! /usr/bin/env python

"""Generates commit data statistics for various VCS.

This script measures team performance of Git and SVN repositories through
the metrics of:

    - frequency of committer,
    - number of lines added,
    - number of lines deleted.
"""

import os
import sys
import shlex
import socket
import logging
import subprocess
import ConfigParser

import psycopg2
import paramiko

import updatenames

from repository import gitstat
from repository import svnstat

LOG_FILE = 'commitstat.log'
LOG_SAVE_DIR = '/var/log/teammetrics'
LOG_FILE_PATH = os.path.join(LOG_SAVE_DIR, LOG_FILE)

CONF_FILE = 'commitinfo.conf'
CONF_FILE_PATH = os.path.join('/etc/teammetrics', CONF_FILE)

SERVER = 'vasks.debian.org'
USER = ''
PASSWORD = ''


def ssh_initialize():
    """Connect to Alioth and return a SSHClient instance."""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    private_key_file = os.path.expanduser('~/.ssh/id_rsa')

    if not os.path.isfile(private_key_file):
        logging.error('Private key file not found OR '
                        'did you provide your Alioth username?')
        sys.exit(1)
    
    try:
        user_key = paramiko.RSAKey.from_private_key_file(private_key_file,
                                                        password=PASSWORD)
    except (paramiko.PasswordRequiredException,
            paramiko.SSHException) as detail:
        logging.error('Please check the key password')
        logging.error(detail)
        sys.exit(1)

    try:
        ssh.connect(SERVER, username=USER, pkey=user_key)
        logging.info('Connection to Alioth successful')
    except (paramiko.SSHException, socket.error) as detail:
        logging.error(detail)
        sys.exit(1)

    return ssh


def get_configuration():
    """Read configuration data of repositories whose logs have to be fetched.
    
    This function returns a list of the teams specified in the configuration
    file. The list is flattened and the section name is stripped.
    """

    config = ConfigParser.SafeConfigParser()
    config.read(CONF_FILE_PATH)
    # Get the names for the mailing lists from the config file.
    sections = config.sections()

    # Create a mapping of the list name to the address(es).
    team_names = {}
    for section in sections:
        teams = []
        # In case the url and lists options are not found, skip the section.
        try:
            team = config.get(section, 'team').splitlines()
        except ConfigParser.NoOptionError as detail:
            logging.error(detail)
            continue
        if not team:
            logging.error('Team option cannot be empty in %s' % section)
            continue

        # Mapping of list-name to list URL (or a list of list-URLs).
        teams.append(team)
        # Flatten the list. 
        teams = sum(teams, [])
        team_names[section] = teams

    if not team_names:
        logging.error('No team(s) found in %s' % CONF_FILE)
        sys.exit(1)

    teams = []
    for section, team_name in team_names.iteritems():
        for each_team in team_name:
            teams.append(each_team)

    return teams


def fetch_vcs(ssh):
    """Returns lists of VCS to their respective team names.

    This function connects to Alioth and fetches the team names in the VCS
    specified which is used to identify the VCS the team is using.
    """

    team_lst = {}
    for each in ('git', 'svn'): 
        cwd = '/{0}'.format(each)
        stdin, stdout, stderr = ssh.exec_command("ls {0}".format(cwd))
        team_lst[each] = stdout.read().splitlines()

    # Get the users registered on Alioth. 
    stdin, stdout, stderr = ssh.exec_command('getent passwd')
    output = stdout.read().splitlines()
    alioth_users = [element.split(':')[4] for element in output] 

    git = team_lst['git']
    svn = team_lst['svn']

    return git, svn, alioth_users


def detect_vcs():
    """Detects which VCS the team is using.

    This function detects which VCS the team is using by SSHing into Alioth
    and checking for the presence of the team in /svn and /git directories.
    Note that some teams use both Git and SVN and that is also handled.
    """

    # Get the team names as a list.
    teams = get_configuration()
    logging.info('Measuring performance of %d teams' % len(teams))
    
    # Initialize the SSHClient instance.
    ssh = ssh_initialize()

    # Get the VCS used by all the teams.
    git, svn, users = fetch_vcs(ssh)
    # Teams that use both SVN and Git.
    svn_and_git = list(set(svn) & set(git))

    # Parse the teams corresponding to their VCS.
    git_lst = list(set(git) & set(teams))
    svn_lst = list(set(svn) & set(teams))
    # Teams using both repositories.
    svn_git_lst = list(set(svn_and_git) & set(teams))

    # Teams which don't use either Git or SVN and will be investigated later.
    all_teams = list(set(git_lst) | set(svn_lst))
    missing_teams = list(set(teams)- set(all_teams))
    if missing_teams:
        logging.warning('Teams not using Git or SVN or are missing: ')
        for each in missing_teams:
            logging.warning('%s' % each)

    return ssh, git_lst, svn_lst, svn_and_git, users


def get_stats():
    """Generate statistics for Git and SVN repositories."""
    ssh, git, svn, svn_git, users = detect_vcs()

    try:
        conn = psycopg2.connect(database='teammetrics')
        cur = conn.cursor()
    except psycopg2.Error as detail:
        logging.error(detail)
        sys.exit(1)

    # First call the Git repositories.
    if git:
        logging.info('There are %d Git repositories' % len(git))
        gitstat.fetch_logs(ssh, conn, cur, git, users)
    else:
        logging.info('No Git repositories found')

    # Now fetch the SVN repositories.
    if svn:
        logging.info('There are %d SVN repositories' % len(svn))
        svnstat.fetch_logs(ssh, conn, cur, svn)
    else:
        logging.info('No SVN repositories found')

    # Update the names.
    updatenames.update_names(conn, cur, table='commitstat')

    cur.close()
    conn.close()
    ssh.close()

    logging.info('Quit')
    sys.exit()


def start_logging():
    """Initialize the logger."""
    logging.basicConfig(filename=LOG_FILE_PATH,
                        level=logging.INFO,
                        format='%(asctime)s %(levelname)s: %(message)s')


if __name__ == '__main__':
    start_logging()
    logging.info('\t\tStarting CommitStat')

    get_stats()
