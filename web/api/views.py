from django.http import HttpResponse
from web.lib import log, lib
from web.api import helper
import json

logger = log.get(__name__)

@lib.respond('JSON')
@lib.jsonify
@lib.versionCheck
def month(request, api_version, team, metric):
    startdate, enddate = lib.dateRange(request)
    data = helper.getMonthData(team, metric, startdate, enddate)
    data['team'] = team
    return data

@lib.respond('JSON')
@lib.jsonify
@lib.versionCheck
def monthAll(request, api_version, team):
    startdate, enddate = lib.dateRange(request)
    data = {}
    data['team'] = team
    data['data'] = []
    data['data'].append(helper.getMonthData(team, 'list', startdate, enddate))
    data['data'].append(helper.getMonthData(team, 'commits', startdate, enddate))
    data['data'].append(helper.getMonthData(team, 'commitlines', startdate, enddate))
    return data

@lib.respond('JSON')
@lib.jsonify
@lib.versionCheck
def monthTopN(request, api_version, team, metric, n):
    """
    Returns monthly data for top N members.
    """
    startdate, enddate = lib.dateRange(request)
    data = helper.getMonthTopNData(team, metric, n, startdate, enddate)
    data['team'] = team
    return data

@lib.respond('JSON')
@lib.jsonify
@lib.versionCheck
def annual(request, api_version, team, metric):
    startdate, enddate = lib.dateRange(request)
    data = helper.getAnnualData(team, metric, startdate, enddate)
    data['team'] = team
    return data

@lib.respond('JSON')
@lib.jsonify
@lib.versionCheck
def annualAll(request, api_version, team):
    startdate, enddate = lib.dateRange(request)
    data = {}
    data['team'] = team
    data['data'] = []
    data['data'].append(helper.getAnnualData(team, 'list', startdate, enddate))
    data['data'].append(helper.getAnnualData(team, 'commits', startdate, enddate))
    data['data'].append(helper.getAnnualData(team, 'commitlines', startdate, enddate))
    return data

@lib.respond('JSON')
@lib.jsonify
@lib.versionCheck
def annualTopN(request, api_version, team, metric, n):
    """
    Returns monthly data for top N members.
    """
    startdate, enddate = lib.dateRange(request)
    data = helper.getAnnualTopNData(team, metric, n, startdate, enddate)
    data['team'] = team
    return data
