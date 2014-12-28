#! /bin/sh -e

DB=teammetrics

# createuser --superuser tille
# createuser --createdb --createrole sukhbir

createdb $DB

psql $DB <<EOF

BEGIN;

CREATE EXTENSION tablefunc;
GRANT EXECUTE ON FUNCTION crosstab(text,text) TO guest;
-- may be this is needed as well
-- GRANT EXECUTE ON FUNCTION crosstab(text) TO guest;
-- GRANT EXECUTE ON FUNCTION crosstab(text,integer) TO guest;

CREATE TABLE listarchives (
    project             text,
    domain              text,
    name                text,
    email_addr          text,
    subject             text,
    message_id          text,
    archive_date        date,
    today_date          date,
    msg_raw_len         int,
    msg_no_blank_len    int,
    msg_no_quotes_len   int,
    msg_no_sig_len      int,
    is_spam             boolean
);

ALTER TABLE listarchives ADD CONSTRAINT PK_project_messageid PRIMARY KEY(project,message_id) ;
ALTER TABLE listarchives ADD COLUMN reference_id text;

CREATE TABLE commitstat (
    commit_id	    	text,
    project             text,
    package             text,
    vcs                 text,
    name                text,
    commit_date		    date,
    today_date		    date,
    lines_inserted      int,
    lines_deleted       int
);

ALTER TABLE commitstat ADD CONSTRAINT PK_commit_id PRIMARY KEY(commit_id, project) ;

-- top N authors of mailing list
CREATE OR REPLACE FUNCTION author_names_of_list(text,int) RETURNS SETOF RECORD AS '
  SELECT name FROM (
    SELECT name, COUNT(*)::int
      FROM listarchives
      WHERE project = \$1
      GROUP BY name
      ORDER BY count DESC
      LIMIT \$2
  ) tmp
' LANGUAGE sql;

/*
SELECT * FROM author_names_of_list('soc-coordination', 12) AS (category text) ;
SELECT * FROM author_names_of_list('debian-med-packaging', 12) AS (category text) ;
 */

CREATE OR REPLACE FUNCTION author_per_year_of_list(text,int) RETURNS SETOF RECORD AS '
  SELECT name, year, COUNT(*)::int FROM (
    SELECT name,  EXTRACT(year FROM archive_date)::int AS year
      FROM listarchives
     WHERE name IN (SELECT * FROM author_names_of_list(\$1, \$2) AS (author text))
       AND project = \$1
  ) tmp
  GROUP BY name, year
  ORDER BY year, count DESC, name
' LANGUAGE sql;

/*
SELECT * FROM author_per_year_of_list('soc-coordination', 12) AS (author text, year int, value int) ;
SELECT * FROM author_per_year_of_list('debian-med-packaging', 12) AS (author text, year int, value int) ;
 */

-- top N authors of commits to project
CREATE OR REPLACE FUNCTION commit_names_of_project(text,int) RETURNS SETOF RECORD AS '
  SELECT name FROM (
    SELECT name, COUNT(*)::int
      FROM commitstat
      WHERE project = \$1
      GROUP BY name
      ORDER BY count DESC
      LIMIT \$2
  ) tmp
' LANGUAGE sql;

/*
SELECT * FROM commit_names_of_project('teammetrics', 12) AS (category text) ;
SELECT * FROM commit_names_of_project('debian-med', 12) AS (category text) ;
 */

CREATE OR REPLACE FUNCTION commmit_per_year_of_project(text,int) RETURNS SETOF RECORD AS '
  SELECT name, year, COUNT(*)::int FROM (
    SELECT name,  EXTRACT(year FROM commit_date)::int AS year
      FROM commitstat
     WHERE name IN (SELECT * FROM commit_names_of_project(\$1, \$2) AS (author text))
       AND project = \$1
  ) tmp
  GROUP BY name, year
  ORDER BY year, count DESC, name
' LANGUAGE sql;

/*
SELECT * FROM commit_per_year_of_project('teammetrics', 12) AS (author text, year int, value int) ;
SELECT * FROM commit_per_year_of_project('debian-med', 12) AS (author text, year int, value int) ;
 */

-- top N commiters per inserted lines of code to project
CREATE OR REPLACE FUNCTION commitlines_names_of_project(text,int,int) RETURNS SETOF RECORD AS '
  SELECT name FROM (
    SELECT name, SUM(lines_inserted)::int AS count
      FROM commitstat
      WHERE project = \$1
       AND lines_inserted < \$3 -- commits with more than \$3 lines are most probably autogenerated
      GROUP BY name
      ORDER BY count DESC
      LIMIT \$2
  ) tmp
' LANGUAGE sql;

/*
SELECT * FROM commitlines_names_of_project('teammetrics', 12, 10000) AS (category text) ;
SELECT * FROM commitlines_names_of_project('debian-med', 12, 10000) AS (category text) ;
 */

CREATE OR REPLACE FUNCTION commmitlines_per_year_of_project(text,int,int) RETURNS SETOF RECORD AS '
  SELECT name, year, SUM(lines_inserted)::int AS count FROM (
    SELECT name,  EXTRACT(year FROM commit_date)::int AS year, lines_inserted
      FROM commitstat
     WHERE name IN (SELECT * FROM commitlines_names_of_project(\$1, \$2, \$3) AS (author text))
       AND project = \$1
       AND lines_inserted < \$3 -- commits with more than \$3 lines are most probably autogenerated
  ) tmp
  GROUP BY name, year
  ORDER BY year, count DESC, name
' LANGUAGE sql;

/*
SELECT * FROM commitlines_per_year_of_project('teammetrics', 12, 10000) AS (author text, year int, value int) ;
SELECT * FROM commitlines_per_year_of_project('debian-med', 12, 10000) AS (author text, year int, value int) ;
 */

GRANT EXECUTE ON FUNCTION author_names_of_list(text,integer) TO guest ;
GRANT SELECT ON listarchives To guest ;
GRANT EXECUTE ON FUNCTION commit_names_of_project(text,integer) TO guest ;
GRANT SELECT ON commitstat To guest ;
GRANT EXECUTE ON FUNCTION commitlines_names_of_project(text,integer,integer) TO guest ;

GRANT ALL ON FUNCTION author_names_of_list(text,integer) TO sukhbir ;
GRANT ALL ON FUNCTION author_names_of_list(text,integer) TO tille ;
GRANT ALL ON listarchives TO sukhbir ;
GRANT ALL ON listarchives TO tille ;
GRANT ALL ON FUNCTION commit_names_of_project(text,integer) TO sukhbir ;
GRANT ALL ON FUNCTION commit_names_of_project(text,integer) TO tille ;
GRANT ALL ON commitstat TO sukhbir ;
GRANT ALL ON commitstat TO tille ;
GRANT ALL ON FUNCTION commitlines_names_of_project(text,integer,integer) TO sukhbir ;
GRANT ALL ON FUNCTION commitlines_names_of_project(text,integer,integer) TO tille ;

COMMIT;
EOF
