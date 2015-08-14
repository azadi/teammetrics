-- BEGIN;

-- maintainers working on single packages (to find out how much the maintainer : package relation is)
-- first argument is the team
-- second enable limiting the number of commits.  Suggested value is 4 which means that all package with only <=4 commits are ignored since the maintenance burden is low anyway
-- third is a limit which requires more commit per maintainer than this limit (to exclude a single contribution for instance)
CREATE OR REPLACE FUNCTION maintainer_per_package(text, int, int) RETURNS SETOF RECORD AS $$
  SELECT panaco.package, CAST(count(*) AS int) FROM (
      SELECT package, name, count(*) as namecount FROM commitstat WHERE project=$1 AND package not in ('', 'meta', 'website') GROUP BY package, name
     ) panaco
    JOIN (SELECT * FROM (SELECT package, count(*) as pkgcount FROM commitstat WHERE project=$1 AND package not in ('', 'meta', 'website') GROUP BY package) paco WHERE pkgcount > $2 ) l ON panaco.package = l.package
    WHERE namecount > $3 GROUP BY panaco.package
$$ LANGUAGE SQL;

-- SELECT * FROM maintainer_per_package('debian-med', 4, 1) AS (package text, maintainernumber int);
-- SELECT * FROM maintainer_per_package('debian-science', 4, 1) AS (package text, maintainernumber int);

CREATE OR REPLACE FUNCTION package_maintenance_numbers(text, int, int) RETURNS SETOF RECORD AS $$
    SELECT maintainernumber, CAST(count(*) AS int) FROM maintainer_per_package($1, $2, $3) AS (package text, maintainernumber int) GROUP BY maintainernumber ORDER BY maintainernumber
$$ LANGUAGE SQL;

-- SELECT * FROM package_maintenance_numbers('debian-med', 4, 1) AS (maintainernumber int, count int);
-- SELECT * FROM package_maintenance_numbers('debian-science', 4, 1) AS (maintainernumber int, count int);

-- maintainer name as argument displays the package he has contributed to and all other people who contributed
CREATE OR REPLACE FUNCTION check_maintainer_contribution(text) RETURNS SETOF RECORD AS $$
    SELECT project, pn.package, name, CAST(count as int) FROM
       (SELECT project, package, name, count(*) as count FROM commitstat WHERE package != '' GROUP BY project, package, name) AS pn
       JOIN (SELECT DISTINCT package FROM commitstat WHERE package != '' AND name = $1) n ON pn.package = n.package
       ORDER BY package, count DESC, project, name
$$ LANGUAGE SQL;

-- SELECT * FROM check_maintainer_contribution('Mathieu Malaterre') AS (project text, package text, name text, ncommit int) ;

CREATE OR REPLACE FUNCTION check_maintainer_contribution_anonymized(text) RETURNS SETOF RECORD AS $$
   SELECT project, package, CASE WHEN name=$1 THEN '-->'||CAST(ncommit AS text) ELSE CAST(ncommit AS text) END FROM check_maintainer_contribution($1) AS (project text, package text, name text, ncommit int)
$$ LANGUAGE SQL;

-- SELECT * FROM check_maintainer_contribution_anonymized('Mathieu Malaterre') AS (project text, package text, ncommit text) ;

-- COMMIT;
