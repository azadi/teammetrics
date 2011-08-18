#!/usr/bin/python
# Copyright 2011: Andreas Tille <tille@debian.org>
# License: GPL

# MAXUPLOADERS=20
MAXUPLOADERS=10

teams = { 
          'debian-med' :       'debian-med-packaging@lists.alioth.debian.org'      ,
          'debian-science':    'debian-science-maintainers@lists.alioth.debian.org',
          'debichem':          'debichem-devel@lists.alioth.debian.org'            ,
          'debian-gis':        'pkg-grass-devel@lists.alioth.debian.org'           ,
          'pkg-multimedia':    'pkg-multimedia-maintainers@lists.alioth.debian.org',
          'pkg-java':          'pkg-java-maintainers@lists.alioth.debian.org'      ,
          'debian-live':       'debian-live@lists.debian.org'                      , # that's no real team but one very active person
          'pkg-perl':          'pkg-perl-maintainers@lists.alioth.debian.org'      ,
          'python-maint':      'pkg-python-debian-maint@lists.alioth.debian.org'   , # that's also no real team
          'python-apps':       'python-apps-team@lists.alioth.debian.org'          ,
          'pkg-phototools':    'pkg-phototools-devel@lists.alioth.debian.org'      ,
          'pkg-scicomp':       'pkg-scicomp-devel@lists.alioth.debian.org'         ,
          'pkg-common-lisp':   'pkg-common-lisp-devel@lists.alioth.debian.org'     ,
          'ocaml-maintainers': 'debian-ocaml-maint@lists.debian.org'               ,
          'pkg-games':         'pkg-games-devel@lists.alioth.debian.org'           ,
          'python-modules':    'python-modules-team@lists.alioth.debian.org'       ,
          'debian-python':     'debian-python@lists.debian.org'                    , # that's only one person
        }

#teams = {
#          'debian-med' :       ('debian-med-packaging@lists.alioth.debian.org',       20),
#          'debian-science':    ('debian-science-maintainers@lists.alioth.debian.org', 35),
#        }

PORT=5441
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

for team in teams.keys():
    datafile='uploaders_'+team+'.txt'
    out = open(datafile, 'w')
    query = "SELECT replace(uploader,' ','_') AS uploader FROM active_uploader_names_of_pkggroup('%s', 1000) AS (uploader text);" % (teams[team])
    # print query
    curs.execute(query)

    print >>out, ' year',
    nuploaders = 0
    for row in curs.fetchall():
        print >>out, '\t' + re.sub('^(.*_\w)[^_]*$', '\\1', row[0]),
        nuploaders += 1
    print >>out, ''

    typestring = 'year text'
    for i in range(nuploaders):
        typestring = typestring + ', upl' + str(i+1) + ' int'
    query = """SELECT *
	FROM 
	crosstab(
	     'SELECT year AS row_name, name AS bucket, count AS value
                     FROM active_uploader_per_year_of_pkggroup(''%s'', %i) AS (name text, year int, count int)',
             'SELECT * FROM active_uploader_names_of_pkggroup(''%s'', %i) AS (category text)'
        ) As (%s)
""" % (teams[team], nuploaders, teams[team], nuploaders, typestring)

    try:
	# print query
        curs.execute(query)
    except psycopg2.ProgrammingError, err:
	if crosstab_missing_re.match(str(err)):
	    print >>stderr, """Please do
	psql udd < /usr/share/postgresql/<pgversion>/contrib/tablefunc.sql
before calling this program."""
	else:
            print >>stderr, "To few uploaders in %s team.\n%s" % (team, err)
	exit(-1)
    for row in curs.fetchall():
        print >>out, ' ' + row[0] ,
        for v in row[1:]:
            if v:
                print >>out, '\t' + str(v),
            else:
                print >>out, '\t0',
        print >>out, ''
    out.close()
    cmdstring='./author_stats_create_graph ' + datafile + ' ' + str(min(nuploaders, MAXUPLOADERS))
    if len(argv) > 1 :
	if argv[1].startswith('pdf'):
	    cmdstring = cmdstring + ' "" pdf'
	if len(argv) > 2:
	    cmdstring = cmdstring + ' ' + argv[2]
    else:
	cmdstring = cmdstring + ' "Uploaders of ' + team + ' team"'
    system(cmdstring)
