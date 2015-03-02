#!/usr/bin/python
# Copyright 2011: Andreas Tille <tille@debian.org>
# License: GPL

# PLOTUPLOADERS=20
PLOTUPLOADERS=10

MAXUPLOADERS=1000

teams = { 
          'debian-astro':      'debian-astro-maintainers@lists.alioth.debian.org'  ,
          'debian-gis':        'pkg-grass-devel@lists.alioth.debian.org'           ,
          'debian-live':       'debian-live@lists.debian.org'                      , # that's no real team but one very active person
          'debian-med' :       'debian-med-packaging@lists.alioth.debian.org'      ,
          'debian-php':        'pkg-php-maint@lists.alioth.debian.org'             ,
          'debian-science':    'debian-science-maintainers@lists.alioth.debian.org',
          'debian-tex':        'debian-tex-maint@lists.debian.org'                 ,
          'debian-xfce':       'pkg-xfce-devel@lists.alioth.debian.org'            ,
          'debichem':          'debichem-devel@lists.alioth.debian.org'            ,
          'ocaml-maintainers': 'debian-ocaml-maint@lists.debian.org'               ,
          'pkg-common-lisp':   'pkg-common-lisp-devel@lists.alioth.debian.org'     ,
          'pkg-exppsy':        'team@neuro.debian.net'                             ,
          'pkg-games':         'pkg-games-devel@lists.alioth.debian.org'           ,
          'pkg-haskell':       'pkg-haskell-maintainers@lists.alioth.debian.org'   ,
          'pkg-java':          'pkg-java-maintainers@lists.alioth.debian.org'      ,
          'pkg-libvirt':       'pkg-libvirt-maintainers@lists.alioth.debian.org'   ,
          'pkg-multimedia':    'pkg-multimedia-maintainers@lists.alioth.debian.org',
          'pkg-openstack':     'openstack-devel@lists.alioth.debian.org'           ,
          'pkg-osm':           'pkg-osm-maint@lists.alioth.debian.org'             ,
          'pkg-perl':          'pkg-perl-maintainers@lists.alioth.debian.org'      ,
          'pkg-phototools':    'pkg-phototools-devel@lists.alioth.debian.org'      ,
          'pkg-ruby':          'pkg-ruby-extras-maintainers@lists.alioth.debian.org',
          'pkg-scicomp':       'pkg-scicomp-devel@lists.alioth.debian.org'         ,
          'python-maint':      'pkg-python-debian-maint@lists.alioth.debian.org'   , # that's also no real team
          'python-apps':       'python-apps-team@lists.alioth.debian.org'          ,
          'python-modules':    'python-modules-team@lists.alioth.debian.org'       ,
        }

#teams = {
#          'debian-med' :       ('debian-med-packaging@lists.alioth.debian.org',       20),
#          'debian-science':    ('debian-science-maintainers@lists.alioth.debian.org', 35),
#        }

PORT=5452
DEFAULTPORT=5432

from sys import argv, stderr, exit
from os import system
import psycopg2
import re

try:
    conn = psycopg2.connect(host="localhost",port=PORT,user="guest",database="udd")
except psycopg2.OperationalError:
    try:
        conn = psycopg2.connect(host="localhost",port=DEFAULTPORT,user="guest",database="udd")
    except psycopg2.OperationalError:
	conn = psycopg2.connect(host="127.0.0.1",port=DEFAULTPORT,user="guest",database="udd")

curs = conn.cursor()

crosstab_missing_re  = re.compile(".* crosstab.*")

def RowDictionaries(cursor):
    """Return a list of dictionaries which specify the values by their column names"""

    description = cursor.description
    if not description:
        # even if there are no data sets to return the description should contain the table structure.  If not something went
        # wrong and we return NULL as to represent a problem
        return NULL
    if cursor.rowcount <= 0:
        # if there are no rows in the cursor we return an empty list
        return []

    data = cursor.fetchall()
    result = []

    for row in data:
        resultrow = {}
        i = 0
        for dd in description:
            resultrow[dd[0]] = row[i]
            i += 1
        result.append(resultrow)
    return result

if argv[0].endswith('upload_history.py'):
    sql_procedure_prefix = 'active_uploader'
    outputname           = 'uploaders'
    title                = 'Uploaders'
    headline             = 'Uploaders of'
    print "Calculate uploaders history"
elif argv[0].endswith('bug_close_history.py'):
    sql_procedure_prefix = 'bug_closer'
    outputname           = 'bugs'
    title                = 'Bugs'
    headline             = 'Bugs closed by'
    print "Calculate bug closing history"
elif argv[0].endswith('sponsor_history.py'):
    sql_procedure_prefix = 'active_sponsor'
    outputname           = 'sponsors'
    title                = 'Sponsors'
    headline             = 'Sponsors of'
    print "Calculate sponsoring history"
else:
    print >>stderr, "Unexpected script name %s" % argv[0]
    exit(1)

for team in teams.keys():
    # print team
    datafile=outputname+'_'+team+'.txt'
    out = open(datafile, 'w')
    query = "SELECT replace(uploader,' ','_') AS uploader FROM %s_names_of_pkggroup('%s', %i) AS (uploader text);" % (sql_procedure_prefix, teams[team], MAXUPLOADERS)
    # print query
    curs.execute(query)

    nuploaders = curs.rowcount
    if nuploaders == 0:
	print >>stderr, "No uploaders found for team %s" % team
	continue

    print >>out, ' year',
    for row in curs.fetchall():
        print >>out, '\t' + re.sub('^(.*_\w)[^_]*$', '\\1', row[0]),
    print >>out, ''

    typestring = 'year text'
    for i in range(nuploaders):
        typestring = typestring + ', upl' + str(i+1) + ' int'
    query = """SELECT *
	FROM 
	crosstab(
	     'SELECT year AS row_name, name AS bucket, count AS value
                     FROM %s_per_year_of_pkggroup(''%s'', %i) AS (name text, year int, count int)',
             'SELECT * FROM %s_names_of_pkggroup(''%s'', %i) AS (category text)'
        ) As (%s)
""" % (sql_procedure_prefix, teams[team], nuploaders, sql_procedure_prefix, teams[team], MAXUPLOADERS, typestring)

    try:
	# print query
        curs.execute(query)
    except psycopg2.ProgrammingError, err:
	if crosstab_missing_re.match(str(err)):
#	    print >>stderr, """Please do
#	psql udd < /usr/share/postgresql/<pgversion>/contrib/tablefunc.sql
#before calling this program."""
	    print >>stderr, "Did you `psql udd -c 'CREATE EXTENSION tablefunc; GRANT EXECUTE ON FUNCTION crosstab(text,text) TO guest;'` before calling this program?\n", err, query, nuploaders
	    exit(-1)
	else:
	    m = re.match(".*\n.*Query-specified return tuple has (\d+) columns but crosstab returns (\d+).*", str(err))
	    nuploaders_calculated = int(m.group(1))
	    nuploaders_returned   = int(m.group(2))
	    # somehow the crosstable returns less columns
	    print >>stderr, "Warning: team %s should have %d uploaders but crosstable returned only %d. Try again with this number." % (team, nuploaders_calculated, nuploaders_returned)
	    typestring = 'year text'
	    for i in range(nuploaders_returned - 1):
    		typestring = typestring + ', upl' + str(i+1) + ' int'
		query = """SELECT *
	FROM 
	crosstab(
	     'SELECT year AS row_name, name AS bucket, count AS value
                     FROM %s_per_year_of_pkggroup(''%s'', %i) AS (name text, year int, count int)',
             'SELECT * FROM %s_names_of_pkggroup(''%s'', %i) AS (category text)'
        ) As (%s)
""" % (sql_procedure_prefix, teams[team], nuploaders, sql_procedure_prefix, teams[team], nuploaders, typestring)
	    # print query
	    conn.rollback()
            curs.execute(query)
    for row in curs.fetchall():
        print >>out, ' ' + row[0] ,
        for v in row[1:]:
            if v:
                print >>out, '\t' + str(v),
            else:
                print >>out, '\t0',
        print >>out, ''
    out.close()
    cmdstring='./author_stats_create_graph ' + datafile + ' ' + str(min(nuploaders, PLOTUPLOADERS))
    if len(argv) > 1 :
	if argv[1].startswith('pdf'):
	    cmdstring = cmdstring + ' "" pdf'
	if len(argv) > 2:
	    cmdstring = cmdstring + ' ' + argv[2]
    else:
	cmdstring = cmdstring + ' "' + headline + ' ' + team + ' team"'
    system(cmdstring)

