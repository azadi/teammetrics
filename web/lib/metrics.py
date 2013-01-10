import ConfigParser
import sys
import os
import web
from web.lib import log
import web.settings as settings

logger = log.get(__name__)

cp = ConfigParser.ConfigParser()

CONF_FILE = os.path.join(os.path.dirname(web.__file__),
                        settings.CONFIG_FILE['metrics'])

def get(metricname, listname):
    logger.info("metrics.get called")
    try:
        cp.readfp(open(CONF_FILE))
    except IOError:
        logger.error("Config File Not Found")
        logger.error("PATH : "+CONF_FILE)
        return []
    else:
        try:
            mlist = cp.get(metricname,listname).split(',')
        except ConfigParser.NoSectionError:
            logger.error("No Such Team")
            return []
        except ConfigParser.NoOptionError:
            logger.error("No Such Metric")
            return []
        else:
            mlist = [name.strip() for name in mlist]
            return mlist

def check_team_exists(team):
    try:
        cp.readfp(open(CONF_FILE))
    except IOError:
        logger.error("Config File Not Found")
        logger.error("PATH : "+CONF_FILE)
        return False
    else:
        return cp.has_section(team)

#TODO: Code needs to be refactored
def check_metric_exist(team,metric):
    try:
        cp.readfp(open(CONF_FILE))
    except IOError:
        logger.error("Config File Not Found")
        logger.error("PATH : "+CONF_FILE)
        return False
    else:
        if metric == 'list':
            metricname = 'list'
        elif metric == 'commits' or metric == 'commitlines':
            metricname = 'repository'
        elif metric == 'uploads':
            metricname = 'bugupload'
        elif metric == 'uploadsname':
            metricname = 'uploadsname'
        elif metric == 'bugs':
            metricname = 'bugupload'
        elif metric == 'bugsname':
            metricname = 'bugsname'
        else:
            logger.info('Incorrect Metric Identifier')
            metricname = ''
        return cp.has_option(team, metricname)

def identify(team, metric):
    """
    Identifies the metric specified in the API using the data in config file.
    Return a list containing the metric name(s) for the team.
    """
    if metric == 'list':
        return get(team,'list')
    elif metric == 'commits':
        return get(team,'repository')
    elif metric == 'commitlines':
        return get(team,'repository')
    elif metric == 'uploads':
        return get(team,'bugupload_key')
    elif metric == 'uploadsname':
        return get(team,'bugupload')
    elif metric == 'bugs':
        return get(team,'bugupload_key')
    elif metric == 'bugsname':
        return get(team,'bugupload')
    else:
        logger.info('Incorrect Metric Identifier')
        return []

def name(metric):
    """
    Returns the metric name as used in the server.
    """
    print metric
    if metric == 'list':
        return 'authorstat'
    elif metric == 'commits':
        return 'commitstat'
    elif metric == 'bugs':
        return 'bugs'
    elif metric == 'uploads':
        return 'uploaders'
    else:
        return ''

def get_all_teams():
    try:
        cp.readfp(open(CONF_FILE))
    except IOError:
        logger.error("Config File Not Found")
        logger.error("PATH : "+CONF_FILE)
        return []
    else:
        return sorted(cp.sections())
