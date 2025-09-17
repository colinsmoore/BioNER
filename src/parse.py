import json
from validate import validate_gene

def parse_segment(segment):
    found_annotations = json.loads(segment)["annotations"]
    found_genes = set()
    found_diseases = set()
    for j in found_annotations:
        if j["obj"] == "gene":
            found_genes.add(j["mention"])
        if j["obj"] == "disease" and j["prob"] > 0.99:
            found_diseases.add(j["mention"])
    return found_genes, found_diseases


def parse_genes(annotations):
    genes_unvalidated = set()
    associated_diseases = {}
    for i in annotations:
        found_genes, found_diseases = parse_segment(i)
        for j in found_genes:
            if j in associated_diseases:
                associated_diseases[j] = associated_diseases[j] | found_diseases
            else:
                associated_diseases[j] = found_diseases
        genes_unvalidated.update(found_genes)
    genes_validated = []
    for i in genes_unvalidated:
        gene = validate_gene(i)
        if gene:
            genes_validated.append(gene)
    return genes_validated, associated_diseases