#! /usr/bin/env python

"""Generates commit data statistics for various VCS.

This script measures team performance of Git and SVN repositories through
the metrics of:

    - frequency of committer,
    - number of lines added,
    - number of lines deleted.

The required data is fetched by SSHing into Alioth.
"""

import logging
import os
import sys
import psycopg2
import urllib
import json    

cachedir='/var/cache/teammetrics/commits'
downloadurl='http://teammetrics.alioth.debian.org/commitstats/'
commits='commits.json'

LOG_FILE = 'commitstat.log'
LOG_SAVE_DIR = '/var/log/teammetrics'
LOG_FILE_PATH = os.path.join(LOG_SAVE_DIR, LOG_FILE)

DATABASE = {
            'name':        'teammetrics',
            'defaultport': 5432,
            'port':        5452, # ... use this on blends.debian.net / udd.debian.net
           }

def start_logging():
    """Initialize the logger."""
    logging.basicConfig(filename=LOG_FILE_PATH,
                        level=logging.INFO,
                        format='%(asctime)s %(levelname)s: %(message)s')

if __name__ == '__main__':

    start_logging()
    logging.info('\t\tStarting CommitStat')

    # get_stats()
    os.system('mkdir -p '+cachedir)

    urllib.urlretrieve (downloadurl+'/'+commits+'.bz2', cachedir+'/'+commits+'.bz2')
    os.system('bunzip2 -f '+cachedir+'/'+commits+'.bz2')

    comfp = open(cachedir+'/'+commits)
    # comfp = open(cachedir+'/zw.json')
    data = json.load(comfp)

    try:
        conn = psycopg2.connect(database=DATABASE['name'])
        cur = conn.cursor()
    except psycopg2.OperationalError:
        try: 
            conn = psycopg2.connect(database=DATABASE['name'], port=DATABASE['port'])
            cur = conn.cursor()
        except psycopg2.Error as detail:
            logging.error(detail)
            sys.exit(1)

    query = "DELETE FROM commitstat"
    cur.execute(query)

    query = """PREPARE svn_insert
      AS INSERT INTO commitstat (commit_id, project, package, vcs, name, commit_date)
      VALUES ($1, $2, $3,  'svn', $4, $5)"""
    try:
        cur.execute(query)
    except psycopg2.ProgrammingError, err:
        print query
        print err
        sys.exit(1)
    query = """PREPARE git_insert
      AS INSERT INTO commitstat (commit_id, project, package, vcs, name, commit_date)
      VALUES ($1, $2, $3, 'git', $4, $5)"""
    cur.execute(query)

    svnquery = "EXECUTE svn_insert (%(commit_id)s, %(project)s, %(package)s, %(name)s, %(commit_date)s)"
    gitquery = "EXECUTE git_insert (%(commit_id)s, %(project)s, %(package)s, %(name)s, %(commit_date)s)"
    for prj in data:
        if prj.has_key('svn'):
            for com in prj['svn']:
                com['project'] = prj['project']
                if not com.has_key('package'):
                    com['package'] = ''
                cur.execute(svnquery, com)
        if prj.has_key('git'):
            for commits in prj['git']:
                for com in commits['commits']:
                    com['project'] = prj['project']
                    com['package'] = commits['package']
                    try:
                        cur.execute(gitquery, com)
                    except psycopg2.IntegrityError, err:
                        print "project:%s, package:%s" % (com['project'], com['package'])
                        print err

    conn.commit()
    cur.close()
    conn.close()
