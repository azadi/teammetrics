-- ATTENTION: the sponsors stuff does not work yet!!!!

-- top 10 maintainers as carnivore ID
CREATE OR REPLACE FUNCTION active_uploader_ids_of_pkggroup(text,int) RETURNS SETOF RECORD AS $$
  SELECT ce.id
         , COUNT(*)::int
    FROM (SELECT source, changed_by_email, nmu FROM upload_history) uh
    JOIN carnivore_emails ce ON ce.email = uh.changed_by_email
   WHERE source IN (           -- source packages that are maintained by the team
       SELECT DISTINCT source FROM upload_history
        WHERE maintainer_email = $1
          AND nmu = 'f'
      )
    AND changed_by_email IN ( -- email of uploaders who at least once uploaded on behalf of the team
       SELECT DISTINCT ce.email FROM upload_history uh
         JOIN carnivore_emails ce ON ce.email = uh.changed_by_email
        WHERE maintainer_email = $1
          AND nmu = 'f'
   )
     AND nmu = 'f'
   GROUP BY ce.id
   ORDER BY count DESC
   LIMIT $2
$$ LANGUAGE SQL;

/*
SELECT * FROM active_uploader_ids_of_pkggroup('debian-med-packaging@lists.alioth.debian.org',50) AS (id int, count int);
SELECT * FROM active_uploader_ids_of_pkggroup('debian-science-maintainers@lists.alioth.debian.org',50) AS (id int, count int);
*/

/* If a packaging group is merged we need to query for a set of maintainer_emails
 */
CREATE OR REPLACE FUNCTION active_uploader_ids_of_pkggroups(text[],int) RETURNS SETOF RECORD AS $$
  SELECT ce.id
         , COUNT(*)::int
    FROM (SELECT source, changed_by_email, nmu FROM upload_history) uh
    JOIN carnivore_emails ce ON ce.email = uh.changed_by_email
   WHERE source IN (           -- source packages that are maintained by the team
       SELECT DISTINCT source FROM upload_history
        WHERE maintainer_email = ANY ($1)
          AND nmu = 'f'
      )
    AND changed_by_email IN ( -- email of uploaders who at least once uploaded on behalf of the team
       SELECT DISTINCT ce.email FROM upload_history uh
         JOIN carnivore_emails ce ON ce.email = uh.changed_by_email
        WHERE maintainer_email = ANY ($1)
          AND nmu = 'f'
   )
     AND nmu = 'f'
   GROUP BY ce.id
   ORDER BY count DESC
   LIMIT $2
$$ LANGUAGE SQL;

/*
SELECT * FROM active_uploader_ids_of_pkggroups('{"pkg-osm-maint@lists.alioth.debian.org","pkg-grass-devel@lists.alioth.debian.org"}',50) AS (id int, count int);
SELECT * FROM active_uploader_ids_of_pkggroups('{"pkg-scicomp-devel@lists.alioth.debian.org","debian-science-maintainers@lists.alioth.debian.org"}',50) AS (id int, count int);
*/

/*
select u.changed_by, signed_by
from upload_history u, carnivore_emails ce1, carnivore_emails ce2
where u.changed_by_email = ce1.email
and u.signed_by_email = ce2.email
and ce1.id != ce2.id
and u.changed_by_email not in (
select email from carnivore_emails, carnivore_login where carnivore_login.id = carnivore_emails.id)
*/

CREATE OR REPLACE FUNCTION active_sponsor_ids_of_pkggroup(text,int) RETURNS SETOF RECORD AS $$
  SELECT ce.id
         , COUNT(*)::int
    FROM (SELECT source, signed_by_email, nmu FROM upload_history) uh
    JOIN carnivore_emails ce ON ce.email = uh.signed_by_email
   WHERE source IN (           -- source packages that are maintained by the team
       SELECT DISTINCT source FROM upload_history
        WHERE maintainer_email = $1
          AND nmu = 'f'
      )
    AND signed_by_email IN ( -- email of sponsors who at least once uploaded on behalf of the team
        SELECT DISTINCT signed_by_email FROM upload_history u, carnivore_emails ce1, carnivore_emails ce2
         WHERE u.changed_by_email = ce1.email
           AND u.signed_by_email = ce2.email
           AND ce1.id != ce2.id
           AND u.changed_by_email NOT IN (
               SELECT email FROM carnivore_emails, carnivore_login WHERE carnivore_login.id = carnivore_emails.id)
           AND maintainer_email = $1
           AND nmu = 'f'
     )
     AND nmu = 'f'
   GROUP BY ce.id
   ORDER BY count DESC
   LIMIT $2
$$ LANGUAGE SQL;

/*
SELECT * FROM active_sponsor_ids_of_pkggroup('debian-med-packaging@lists.alioth.debian.org',50) AS (id int, count int);
SELECT * FROM active_sponsor_ids_of_pkggroup('debian-science-maintainers@lists.alioth.debian.org',50) AS (id int, count int);
*/

-- top 10 maintainers with acticity per year
-- Remark: There is no need to transform carnivore IDs into names because the calling functions needs to
--         recreate table header anyway
CREATE OR REPLACE FUNCTION active_uploader_per_year_of_pkggroup(text,int) RETURNS SETOF RECORD AS $$
  SELECT cn.name, uh.year, COUNT(*)::int FROM
    (SELECT source, EXTRACT(year FROM date)::int AS year, changed_by_email
       FROM upload_history
      WHERE nmu = 'f'
    ) uh
    JOIN carnivore_emails ce ON ce.email = uh.changed_by_email
    JOIN (SELECT * FROM carnivore_names
           WHERE id IN (SELECT idupl FROM active_uploader_ids_of_pkggroup($1, $2) AS (idupl int, count int))
    )  cn ON ce.id    = cn.id
    JOIN carnivore_names_prefered cnp ON cn.id = cnp.id
   WHERE source IN (           -- source packages that are maintained by the team
      SELECT DISTINCT source FROM upload_history
      WHERE maintainer_email = $1
        AND nmu = 'f'
     )
     AND changed_by_email IN ( -- email of uploaders who at least once uploaded on behalf of the team
      SELECT DISTINCT ce.email FROM upload_history uh
        JOIN carnivore_emails ce ON ce.email = uh.changed_by_email
       WHERE maintainer_email = $1
     )
     AND cn.name = cnp.name
   GROUP BY cn.name, uh.year
   ORDER BY year, count DESC, cn.name
$$ LANGUAGE SQL;

/*
SELECT * FROM active_uploader_per_year_of_pkggroup('debian-med-packaging@lists.alioth.debian.org',50) AS (name text, year int, count int);
SELECT * FROM active_uploader_per_year_of_pkggroup('debian-science-maintainers@lists.alioth.debian.org',50) AS (name text, year int, count int);
*/

-- top 10 maintainers with acticity per year for a set of maintainer_emails
CREATE OR REPLACE FUNCTION active_uploader_per_year_of_pkggroups(text[],int) RETURNS SETOF RECORD AS $$
  SELECT cn.name, uh.year, COUNT(*)::int FROM
    (SELECT source, EXTRACT(year FROM date)::int AS year, changed_by_email
       FROM upload_history
      WHERE nmu = 'f'
    ) uh
    JOIN carnivore_emails ce ON ce.email = uh.changed_by_email
    JOIN (SELECT * FROM carnivore_names
           WHERE id IN (SELECT idupl FROM active_uploader_ids_of_pkggroups($1, $2) AS (idupl int, count int))
    )  cn ON ce.id    = cn.id
    JOIN carnivore_names_prefered cnp ON cn.id = cnp.id
   WHERE source IN (           -- source packages that are maintained by the team
      SELECT DISTINCT source FROM upload_history
      WHERE maintainer_email = ANY ($1)
        AND nmu = 'f'
     )
     AND changed_by_email IN ( -- email of uploaders who at least once uploaded on behalf of the team
      SELECT DISTINCT ce.email FROM upload_history uh
        JOIN carnivore_emails ce ON ce.email = uh.changed_by_email
       WHERE maintainer_email = ANY ($1)
     )
     AND cn.name = cnp.name
   GROUP BY cn.name, uh.year
   ORDER BY year, count DESC, cn.name
$$ LANGUAGE SQL;

/*
SELECT * FROM active_uploader_per_year_of_pkggroups('{"pkg-osm-maint@lists.alioth.debian.org","pkg-grass-devel@lists.alioth.debian.org"}',50) AS (name text, year int, count int);
SELECT * FROM active_uploader_per_year_of_pkggroups('{"pkg-scicomp-devel@lists.alioth.debian.org","debian-science-maintainers@lists.alioth.debian.org"}',50) AS (name text, year int, count int);
*/

-- top 10 sponsors with acticity per year
CREATE OR REPLACE FUNCTION active_sponsor_per_year_of_pkggroup(text,int) RETURNS SETOF RECORD AS $$
  SELECT cn.name, uh.year, COUNT(*)::int FROM
    (SELECT source, EXTRACT(year FROM date)::int AS year, signed_by_email
       FROM upload_history
      WHERE nmu = 'f'
    ) uh
    JOIN carnivore_emails ce ON ce.email = uh.signed_by_email
    JOIN (SELECT * FROM carnivore_names
           WHERE id IN (SELECT idupl FROM active_sponsor_ids_of_pkggroup($1, $2) AS (idupl int, count int))
    )  cn ON ce.id    = cn.id
    JOIN carnivore_names_prefered cnp ON cn.id = cnp.id
   WHERE source IN (           -- source packages that are maintained by the team
      SELECT DISTINCT source FROM upload_history
      WHERE maintainer_email = $1
        AND nmu = 'f'
     )
     AND signed_by_email IN ( -- email of sponsors who at least once uploaded on behalf of the team
/* FIXME:  This does not work that way!!!
        SELECT DISTINCT signed_by_email FROM upload_history u, carnivore_emails ce1, carnivore_emails ce2
         WHERE u.changed_by_email = ce1.email
           AND u.signed_by_email = ce2.email
           AND ce1.id != ce2.id
           AND u.changed_by_email NOT IN (
               SELECT email FROM carnivore_emails, carnivore_login WHERE carnivore_login.id = carnivore_emails.id)
           AND maintainer_email = $1
           AND nmu = 'f'
 */
      SELECT DISTINCT ce.email FROM upload_history uh
        JOIN carnivore_emails ce ON ce.email = uh.signed_by_email
       WHERE maintainer_email = $1
     )
     AND cn.name = cnp.name
   GROUP BY cn.name, uh.year
   ORDER BY year, count DESC, cn.name
$$ LANGUAGE SQL;

/*
SELECT * FROM active_sponsor_per_year_of_pkggroup('debian-med-packaging@lists.alioth.debian.org',50) AS (name text, year int, count int);
SELECT * FROM active_sponsor_per_year_of_pkggroup('debian-science-maintainers@lists.alioth.debian.org',50) AS (name text, year int, count int);
*/

-- top 10 maintainers as (hopefully!!!) unique name
CREATE OR REPLACE FUNCTION active_uploader_names_of_pkggroup(text, int) RETURNS SETOF RECORD AS $$
  SELECT cnp.name FROM
    (SELECT id FROM active_uploader_ids_of_pkggroup($1, $2) AS (id int, count int)) au
    JOIN carnivore_names_prefered cnp ON au.id = cnp.id
$$ LANGUAGE SQL;

/*
SELECT * FROM active_uploader_names_of_pkggroup('debian-med-packaging@lists.alioth.debian.org',50) AS (name text);
SELECT * FROM active_uploader_names_of_pkggroup('debian-science-maintainers@lists.alioth.debian.org',50) AS (name text);
*/

-- top 10 maintainers as (hopefully!!!) unique name for more than one team
CREATE OR REPLACE FUNCTION active_uploader_names_of_pkggroups(text[], int) RETURNS SETOF RECORD AS $$
  SELECT cnp.name FROM
    (SELECT id FROM active_uploader_ids_of_pkggroups($1, $2) AS (id int, count int)) au
    JOIN carnivore_names_prefered cnp ON au.id = cnp.id
$$ LANGUAGE SQL;

/*
SELECT * FROM active_uploader_names_of_pkggroups('{"pkg-osm-maint@lists.alioth.debian.org","pkg-grass-devel@lists.alioth.debian.org"}',50) AS (name text);
SELECT * FROM active_uploader_names_of_pkggroups('{"pkg-scicomp-devel@lists.alioth.debian.org","debian-science-maintainers@lists.alioth.debian.org"}',50) AS (name text);
*/

-- top 10 sponsors as (hopefully!!!) unique name
CREATE OR REPLACE FUNCTION active_sponsor_names_of_pkggroup(text, int) RETURNS SETOF RECORD AS $$
  SELECT cnp.name FROM
    (SELECT id FROM active_sponsor_ids_of_pkggroup($1, $2) AS (id int, count int)) au
    JOIN carnivore_names_prefered cnp ON au.id = cnp.id
$$ LANGUAGE SQL;

/*
SELECT * FROM active_sponsor_names_of_pkggroup('debian-med-packaging@lists.alioth.debian.org',50) AS (name text);
SELECT * FROM active_sponsor_names_of_pkggroup('debian-science-maintainers@lists.alioth.debian.org',50) AS (name text);
*/

/*
 Finally you need to

   psql udd -c 'CREATE EXTENSION tablefunc;'

 to be able to run uploader statistics script
 */
