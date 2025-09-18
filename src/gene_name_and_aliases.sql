SELECT g.name, GROUP_CONCAT(a.alias_name, ', ') as aliasn_names
FROM Gene AS g 
JOIN Alias AS a on a.gene_id = g.hgnc_id
GROUP BY g.name;