from web.models import listarchives, commitstat, commitlines
from web.lib import metrics
from web.lib import metrics, log
from web.api import settings

logger = log.get(__name__)

def checkKeyValueExist(dlist, key, value):
    """
    Check if a dictionary with a particular given key-value exists in a given 
    list of dictionaries.
    """
    for d in dlist:
        if d.has_key(key):
            if d[key]==value:
                return dlist.index(d)
    return -1

def keyValueIndex(data, key, value):
    """
    Check if a dictionary with a particular given key-value exists in a given 
    list of dictionaries, if yes, returns the index of the dictionary, if no, 
    inserts and returns the index.
    """
    d = checkKeyValueExist(data, key, value)
    if d == -1 :
        kv = {}
        kv[key] = value
        data.append(kv)
        d=len(data)-1
    return d

def processMonthData(dbdata, metriclist):
    data = {'annualdata' : []}
    for i in dbdata:
        d = keyValueIndex(data['annualdata'],'year',int(float(i[0])))
        if not data['annualdata'][d].has_key('monthlydata'):
            data['annualdata'][d]['monthlydata']=[]
            
        metricdata={}
        metricdata['month'] = int(float(i[1]))
        metricdata[metriclist[0]] = int(float(i[2]))
        try:
            metricdata[metriclist[1]] = int(float(i[3]))
        except IndexError:
            pass
        data['annualdata'][d]['monthlydata'].append(metricdata)
    return data

def processMonthTopNData(dbdata, metriclist):
    data = {'annualdata' : []}
    for i in dbdata:
        d = keyValueIndex(data['annualdata'],'year',int(float(i[0])))
        if not data['annualdata'][d].has_key('monthlydata'):
            data['annualdata'][d]['monthlydata']=[]
        u = keyValueIndex(data['annualdata'][d]['monthlydata'],'month',int(float(i[1])))
        if not data['annualdata'][d]['monthlydata'][u].has_key('userdata'):
            data['annualdata'][d]['monthlydata'][u]['userdata']=[]
        userdata = {}
        userdata['name'] = i[2]
        userdata[metriclist[0]] = int(float(i[3]))
        try:
            userdata[metriclist[1]] = int(float(i[4]))
        except IndexError:
            pass
        data['annualdata'][d]['monthlydata'][u]['userdata'].append(userdata)
    return data

def processAnnualData(dbdata, metriclist):
    data = {'annualdata' : []}
    for i in dbdata:
        metricdata = {}
        metricdata['year'] = int(float(i[0]))
        metricdata[metriclist[0]] = int(float(i[1]))
        try:
            metricdata[metriclist[1]] = int(float(i[2]))
        except IndexError:
            pass
        data['annualdata'].append(metricdata)
    return data

def processAnnualTopNData(dbdata, metriclist):
    data = {'annualdata' : []}
    for i in dbdata:
        d = keyValueIndex(data['annualdata'], 'year', int(float(i[0])))
        if not data['annualdata'][d].has_key('userdata'):
            data['annualdata'][d]['userdata'] = []
        userdata = {}
        userdata['name'] = i[1]
        userdata[metriclist[0]] = int(float(i[2]))
        try:
            userdata[metriclist[1]] = int(float(i[3]))
        except IndexError:
            pass
        data['annualdata'][d]['userdata'].append(userdata)
    return data

def monthList(team, mlist, startdate, enddate):
    dbdata=listarchives.monthData(mlist, startdate, enddate)
    data = processMonthData(dbdata, ['liststat'])
    data['mailing-list'] = mlist
    return data

def monthCommits(team, repo,  startdate, enddate):
    dbdata=commitstat.monthData(repo, startdate, enddate)
    data=processMonthData(dbdata, ['commits'])
    data['repository'] = repo
    return data

def monthCommitLines(team, repo, startdate, enddate):
    dbdata=commitlines.monthData(repo, startdate, enddate)
    data=processMonthData( dbdata, ['lines_added', 'lines_removed'])
    data['repository'] = repo
    return data

def monthTopNList(team, mlist, n, startdate, enddate):
    dbdata=listarchives.monthTopN(mlist, n, startdate, enddate)
    data = processMonthTopNData(dbdata, ['liststat'])
    data['mailing-list'] = mlist
    return data

def monthTopNCommits(team, repo, n, startdate, enddate):
    dbdata=commitstat.monthTopN(repo, n, startdate, enddate)
    data=processMonthTopNData(dbdata, ['commits'])
    data['repository'] = repo
    return data

def monthTopNCommitLines(team, repo, n, startdate, enddate):
    dbdata=commitlines.monthTopN(repo, n)
    data=processMonthTopNData(dbdata, ['lines_added', 'lines_removed'])
    data['repository'] = repo
    return data

def annualList(team, mlist, startdate, enddate):
    dbdata=listarchives.annualData(mlist, startdate, enddate)
    data = processAnnualData(dbdata, ['liststat'])
    data['mailing-list'] = mlist
    return data

def annualCommits(team, repo, startdate, enddate):
    dbdata=commitstat.annualData(repo, startdate, enddate)
    data=processAnnualData(dbdata, ['commits'])
    data['repository'] = repo
    return data

def annualCommitLines(team, repo, startdate, enddate):
    dbdata=commitlines.annualData(repo, startdate, enddate)
    data=processAnnualData( dbdata, ['lines_added', 'lines_removed'])
    data['repository'] = repo
    return data

def annualTopNList(team, mlist, n, startdate, enddate):
    dbdata=listarchives.annualTopN(mlist, n, startdate, enddate)
    data = processAnnualTopNData(dbdata, ['liststat'])
    data['mailing-list'] = mlist
    return data

def annualTopNCommits(team, repo, n, startdate, enddate):
    dbdata=commitstat.annualTopN(repo, n, startdate, enddate)
    data=processAnnualTopNData(dbdata, ['commits'])
    data['repository'] = repo
    return data

def annualTopNCommitLines(team, repo, n, startdate, enddate):
    dbdata=commitlines.annualTopN(repo, n, startdate, enddate)
    data=processAnnualTopNData(dbdata, ['lines_added', 'lines_removed'])
    data['repository'] = repo
    return data

def getMonthData(team, metric, startdate=None, enddate=None):
    """
    Returns JSON ready monthly data for a given team and metric.
    """
    metricname = metrics.identify(team, metric)
    data = {'metric' : metric}
    if metric == 'list':
        data['data'] = [monthList(team,m, startdate, enddate) for m in metricname]
    elif metric == 'commits':
        data['data'] = [monthCommits(team,m, startdate, enddate) for m in metricname]
    elif metric == 'commitlines':
        data['data'] = [monthCommitLines(team,m, startdate, enddate) for m in metricname]
    return data

def getMonthTopNData(team, metric, n,  startdate=None, enddate=None):
    """
    Returns JSON ready monthly top N data for a given team and metric.
    """
    metricname = metrics.identify(team, metric)
    data = {'metric' : metric}
    if metric == 'list':
        data['data'] = [monthTopNList(team,m,n, startdate, enddate) for m in metricname]
    elif metric == 'commits':
        data['data'] = [monthTopNCommits(team,m,n, startdate, enddate) for m in metricname]
    elif metric == 'commitlines':
        data['data'] = [monthTopNCommitLines(team,m,n) for m in metricname]
    return data

def getAnnualData(team, metric,  startdate=None, enddate=None):
    """
    Returns JSON ready monthly data for a given team and metric.
    """
    metricname = metrics.identify(team, metric)
    data = {'metric' : metric}
    if metric == 'list':
        data['data'] = [annualList(team,m, startdate, enddate) for m in metricname]
    elif metric == 'commits':
        data['data'] = [annualCommits(team,m, startdate, enddate) for m in metricname]
    elif metric == 'commitlines':
        data['data'] = [annualCommitLines(team,m, startdate, enddate) for m in metricname]
    return data

def getAnnualTopNData(team, metric, n,  startdate=None, enddate=None):
    """
    Returns JSON ready monthly top N data for a given team and metric.
    """
    metricname = metrics.identify(team, metric)
    data = {'metric' : metric}
    if metric == 'list':
        data['data'] = [annualTopNList(team,m,n, startdate, enddate) for m in metricname]
    elif metric == 'commits':
        data['data'] = [annualTopNCommits(team,m,n, startdate, enddate) for m in metricname]
    elif metric == 'commitlines':
        data['data'] = [annualTopNCommitLines(team,m,n, startdate, enddate) for m in metricname]
    return data
