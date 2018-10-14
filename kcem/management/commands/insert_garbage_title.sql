INSERT
IGNORE INTO garbage_title (page_title)
SELECT DISTINCT page_title
FROM page
WHERE (page_namespace IN (0,
                          14)
       AND page_id IN
         (SELECT pp_page
          FROM page_props
          WHERE pp_propname='hiddencat'))
  OR page_namespace=4;