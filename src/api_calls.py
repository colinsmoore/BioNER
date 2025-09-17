import requests
from xml.etree import ElementTree
import json

def fetch_pubmed_text(pmid):
    url = f"https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_xml/{pmid}/ascii"
    response = requests.get(url)
    root = ElementTree.fromstring(response.content)
    texts = []
    target_section_types = ["ABSTRACT", "INTRO", "RESULTS", "DISCUSS", "CONCL"]
    target_types = ["abstract", "paragraph"]
    for segment in root.iter("passage"):
        section_type = segment.find(".//infon[@key='section_type']")
        type = segment.find(".//infon[@key='type']")
        if type.text in target_types and section_type.text in target_section_types:
            texts.append(segment.find("text").text)
    return texts

def get_annotations(text):
    url = "http://bern2.korea.ac.kr/plain"
    annotations = []
    for i in text:
        data = {"text": i}
        response = requests.post(url, json=data)
        annotations.append(response.text)
    return annotations

def get_genomic_coordinates(gene, reference):
    url = f"https://mygene.info/v3/query?q={gene}&fields={reference}&species=human"
    response = requests.get(url)
    result = json.loads(response.content)
    genomic_pos = result["hits"][0][reference]
    if isinstance(genomic_pos, list):
        chr = genomic_pos[0]["chr"],
        start = genomic_pos[0]["start"],
        end = genomic_pos[0]["end"],
    else:
        chr = genomic_pos["chr"],
        start = genomic_pos["start"],
        end = genomic_pos["end"],

    return {
        "chr": chr,
        "start": start,
        "end": end,
    }

def get_gene_info(gene):
    url = f"https://rest.genenames.org/fetch/symbol/{gene}"
    response = requests.get(url)
    return ElementTree.fromstring(response.content)