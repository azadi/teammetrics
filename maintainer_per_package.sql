-- BEGIN;

-- maintainers working on single packages (to find out how much the maintainer : package relation is)
-- first argument is the team
-- second enable limiting the number of commits.  Suggested value is 4 which means that all package with only <=4 commits are ignored since the maintenance burden is low anyway
-- third is a limit which requires more commit per maintainer than this limit (to exclude a single contribution for instance)
CREATE OR REPLACE FUNCTION maintainer_per_package(text, int, int) RETURNS SETOF RECORD AS $$
  SELECT panaco.package, CAST(count(*) AS int) FROM (
      SELECT package, name, count(*) as namecount FROM commitstat WHERE project=$1 AND package != '' GROUP BY package, name
     ) panaco
    JOIN (SELECT * FROM (SELECT package, count(*) as pkgcount FROM commitstat WHERE project=$1 AND package != '' GROUP BY package) paco WHERE pkgcount > $2 ) l ON panaco.package = l.package
    WHERE namecount > $3 GROUP BY panaco.package
$$ LANGUAGE SQL;

-- SELECT * FROM maintainer_per_package('debian-med', 4, 1) AS (package text, maintainernumber int);
-- SELECT * FROM maintainer_per_package('debian-science', 4, 1) AS (package text, maintainernumber int);

CREATE OR REPLACE FUNCTION package_maintenance_numbers(text, int, int) RETURNS SETOF RECORD AS $$
    SELECT maintainernumber, CAST(count(*) AS int) FROM maintainer_per_package($1, $2, $3) AS (package text, maintainernumber int) GROUP BY maintainernumber ORDER BY maintainernumber
$$ LANGUAGE SQL;

-- SELECT * FROM package_maintenance_numbers('debian-med', 4, 1) AS (maintainernumber int, count int);
-- SELECT * FROM package_maintenance_numbers('debian-science', 4, 1) AS (maintainernumber int, count int);

-- COMMIT;
