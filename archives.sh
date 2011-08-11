#! /bin/sh

DB=teammetrics

createdb $DB
psql $DB < /usr/share/postgresql/9.0/contrib/tablefunc.sql

psql $DB <<EOF

BEGIN;

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
    msg_no_sig_len      int
);

ALTER TABLE listarchives ADD CONSTRAINT PK_project_messageid PRIMARY KEY(project,message_id) ;

CREATE TABLE commitstat (
    commit_id		    text,
    project             text,
    package             text,
    vcs                 text,
    name                text,
    changes             int,
    lines_inserted      int,
    lines_deleted       int
);

ALTER TABLE commitstat ADD CONSTRAINT PK_commit_id PRIMARY KEY(commit_id, project) ;

CREATE TABLE listspam (
    message_id          text,
    project             text,
    name                text,
    email_addr          text,
    subject             text,
    reason              text
);

ALTER TABLE listspam ADD CONSTRAINT PK_spam_messageid PRIMARY KEY(message_id) ;

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
' LANGUAGE 'SQL';

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
' LANGUAGE 'SQL';

/*
SELECT * FROM author_per_year_of_list('soc-coordination', 12) AS (author text, year int, value int) ;
SELECT * FROM author_per_year_of_list('debian-med-packaging', 12) AS (author text, year int, value int) ;
 */


COMMIT;
EOF