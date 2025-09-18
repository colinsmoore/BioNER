SELECT g.hgnc_id, GROUP_CONCAT(d.disease, ', ') AS diseases
FROM Gene AS g
JOIN GeneDisease AS gd on gd.gene_id = g.hgnc_id
JOIN Disease AS d on d.id = gd.disease_id
GROUP BY g.hgnc_id;