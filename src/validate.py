from api_calls import get_gene_info, get_genomic_coordinates

def validate_gene(gene):
    root = get_gene_info(gene)
    result = root.find(".//result[@numFound='1']")
    if result is not None:
        hgncId = result.find(".//str[@name='hgnc_id']").text
        hgncName = result.find(".//str[@name='name']").text
        alias = result.find(".//arr[@name='alias_name']")
        alias_names = []
        if alias is not None:
            for i in alias.iter('str'):
                alias_names.append(i.text)
        hg38_pos = get_genomic_coordinates(gene, "genomic_pos")
        hg19_pos = get_genomic_coordinates(gene, "genomic_pos_hg19")
        # Need to use USCS for hg19 location for the gene. Doesn't seem to exist for the HGNC api
        return {"hgnc_id": hgncId, "name": hgncName, "alias": alias_names, "hg38_pos": hg38_pos, "hg19_pos": hg19_pos}
    else:
        return False