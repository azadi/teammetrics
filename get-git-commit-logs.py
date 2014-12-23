#!/usr/bin/python

import ast
import logging
import json
import os
import re
import sys
import subprocess
import ConfigParser

webdir='/srv/alioth.debian.org/chroot/home/groups/teammetrics/htdocs/commitstats'
webdir='.' ## FIXME
outputfile=webdir+'/git-commits.json'

LOG_FILE = 'commitstat.log'
LOG_SAVE_DIR = os.path.expanduser("~")+ '/log'
LOG_FILE_PATH = os.path.join(LOG_SAVE_DIR, LOG_FILE)

CONF_FILE = 'commitinfo.conf'
CONF_FILE_PATH = os.path.join(os.path.expanduser("~") + '/etc/teammetrics', CONF_FILE)

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
        # Flatten the list..
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

def start_logging():
    """Initialize the logger."""
    logging.basicConfig(filename=LOG_FILE_PATH,
                        level=logging.INFO,
                        format='%(asctime)s %(levelname)s: %(message)s')

def get_git_commits(project):
    data=[]
    gitbase='/git/'+project
    if not os.path.isdir(gitbase):
        logging.warning('No such directory %s.  Ignore Git repositories of %s.' % (gitbase, project))
        return []
    gitdirs=os.popen('find %s -name "*[-a-z0-9+].git" 2>/dev/null' % gitbase)
    for gitr in gitdirs.readlines():
        gdata = {}
        gitr = gitr.strip()
        if not os.path.isdir(gitr) and not os.path.islink(gitr):  ##  FIXME: islink needs to be removed after testing!!!!!
            logging.error('%s is no directory.' % gitr)
            continue
        package = re.sub("^.*/([^/]*)\.git", '\\1', gitr)
        gdata['package'] = package
        gdata['commits'] = []
        gcmd=['git', 'log', '--no-merges', '--date=short', '--pretty=format:''{"commit_id":"%H", "name":"%an", "e-mail":"%ae", "commit_date":"%ad"}''', '--', 'debian'] # >> $data 2>/dev/null'
        # print gitr
        gitcom = subprocess.Popen(gcmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=gitr)
        gitcom.wait()
        (stdoutdata, stderrdata) = gitcom.communicate()
        for com in stdoutdata.split('\n'):
            commit = ast.literal_eval(com)
            # print commit
            gdata['commits'].append(commit)
        data.append(gdata)
    return data

if __name__ == '__main__':
    start_logging()
    logging.info('\t\tStarting CommitStat')

    teams = get_configuration()
    logging.info('Measuring performance of %d teams' % len(teams))
    gitdata=[]
    for project in teams:
        data = {}
        data['project'] = project
        gd = get_git_commits(project)
        if not gd:
            continue
        data['git'] = gd
        gitdata.append(data)
    f = open(outputfile, 'w')
    print >>f, json.dumps(gitdata)
    f.close()
