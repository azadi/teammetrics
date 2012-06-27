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
    else:
        logger.info('Incorrect Metric Identifier')
        return []