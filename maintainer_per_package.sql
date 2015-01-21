-- BEGIN;

-- maintainers working on single packages (to find out how much the maintainer : package relation is)
-- first argument is the team
-- second is a limit which requires more commit per maintainer than this limit (to exclude a single contribution for instance
CREATE OR REPLACE FUNCTION maintainer_per_package(text, int) RETURNS SETOF RECORD AS $$
  SELECT package, CAST(count(*) AS int) FROM (
      SELECT package, name, count(*) as count FROM commitstat WHERE project=$1 AND package != '' GROUP BY package, name
     ) AS panaco
    WHERE count > $2 GROUP BY package ORDER BY count desc, package
$$ LANGUAGE SQL;

-- SELECT * FROM maintainer_per_package('debian-med', 1) AS (package text, maintainernumber int);
-- SELECT * FROM maintainer_per_package('debian-science', 1) AS (package text, maintainernumber int);

CREATE OR REPLACE FUNCTION package_maintenance_numbers(text, int) RETURNS SETOF RECORD AS $$
    SELECT maintainernumber, CAST(count(*) AS int) FROM maintainer_per_package($1, $2) AS (package text, maintainernumber int) GROUP BY maintainernumber ORDER BY maintainernumber
$$ LANGUAGE SQL;

SELECT * FROM package_maintenance_numbers('debian-med', 1) AS (maintainernumber int, count int);
SELECT * FROM package_maintenance_numbers('debian-science', 1) AS (maintainernumber int, count int);

-- COMMIT;
