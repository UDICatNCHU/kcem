SELECT p.page_title,
       c.cl_to
FROM categorylinks c
INNER JOIN page p ON c.cl_from = p.page_id
WHERE p.page_namespace IN (0,
                           14)
  AND c.cl_to NOT IN
    (SELECT *
     FROM garbage_title);