from web.models import listarchives, commitstat, commitlines, uploadstats

def getTopNNames(team, metric, n=10):
    if metric == 'list':
        return listarchives.getTopN(team)
    elif metric == 'commits':
        return commitstat.getTopN(team)
    elif metric == 'commitlines':
        return commitlines.getTopN(team)
    elif metric == 'uploads':
        return uploadstats.getTopN(team)
    else:
        return []
