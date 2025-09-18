import asyncio
import argparse
from prisma import Prisma
from prisma.errors import PrismaError
import json
import requests
from xml.etree import ElementTree

# Formatting functions
def format_diseases(existing_diseases, new_diseases):
    return list(set(existing_diseases) | set(new_diseases))

def format_genes(genes, segment_genes, segment_disease):
    for i in segment_genes:
        if i in genes:
            genes[i]["diseases"] = format_diseases(genes[i]["diseases"], segment_disease)
        else:
            genes[i] = fetch_gene_info(i, segment_disease)
    return genes

# Parsing functions
def parse_annotations(annotations):
    genes, diseases = set(), set()
    for annotation in annotations.iter("annotation"):
        annotation_type = annotation.find(".//infon[@key='type']")
        if annotation_type.text == "Gene":
            genes.add(annotation.find(".//infon[@key='identifier']").text)
        elif annotation_type.text == "Disease":
            diseases.add(annotation.find("text").text)
    return genes, diseases

# API calls

def execute_api_call(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response
    except requests.exceptions.HTTPError as e:
        raise SystemExit(e)
    except requests.exceptions.RequestException as e:
        raise SystemExit(e)

def fetch_pubmed_annotations(pmid):
    url = f"https://www.ncbi.nlm.nih.gov/research/pubtator3-api/publications/export/biocxml?pmids={pmid}&full=true"
    response = execute_api_call(url)
    root = ElementTree.fromstring(response.content)
    genes = {}
    target_section_types = ["ABSTRACT", "INTRO", "RESULTS", "DISCUSS", "CONCL"]
    target_types = ["abstract", "paragraph"]
    for segment in root.iter("passage"):
        section_type = segment.find(".//infon[@key='section_type']")
        type = segment.find(".//infon[@key='type']")
        if type.text in target_types and section_type.text in target_section_types:
            segment_genes, segment_disease = parse_annotations(segment)
            genes = format_genes(genes, segment_genes, segment_disease)
    return genes

def fetch_gene_info(gene, diseases):
    url = f"https://mygene.info/v3/gene/{gene}"
    response = execute_api_call(url)
    gene_info = json.loads(response.content)
    hgnc_id = gene_info["HGNC"]
    name = gene_info["name"]
    gene_aliases = gene_info["other_names"]
    hg38_pos = gene_info["genomic_pos"]
    if isinstance(hg38_pos, list):
        hg38_pos = hg38_pos[0]
    hg19_pos = gene_info["genomic_pos_hg19"]
    if isinstance(hg19_pos, list):
        hg19_pos = hg19_pos[0]
    return {
        "hgnc_id": hgnc_id,
        "name": name,
        "aliases": gene_aliases,
        "hg38": hg38_pos,
        "hg19": hg19_pos,
        "diseases": diseases
    }

# SQL functions
async def save_genes_to_db(db, genes):
    for _, info in genes.items():
        hgnc = info.get("hgnc_id")
        name = info.get("name")
        hg38 = info.get("hg38")
        hg19 = info.get("hg19")

        hg38_id = None
        hg19_id = None

        # Create position records
        try:
            rec = await db.gene_position.create(
                data={
                    "chr": hg38.get("chr"),
                    "start": hg38.get("start"),
                    "end": hg38.get("end"),
                    "strand": hg38.get("strand")
                }
            )
            hg38_id = rec.id
        except PrismaError:
            hg38_id = None
        try:
            rec = await db.gene_position.create(
                data={
                    "chr": hg19.get("chr"),
                    "start": hg19.get("start"),
                    "end": hg19.get("end"),
                    "strand": hg19.get("strand")
                }
            )
            hg19_id = rec.id
        except PrismaError as e:
            print(f"No record created: {e}")
            hg19_id = None

        alias_create = [{"alias_name": a} for a in info.get("aliases")]

        # Upsert gene
        try:
            await db.gene.upsert(
                where={"hgnc_id": hgnc},
                data={
                    "create": {
                        "hgnc_id": hgnc,
                        "name": name,
                        "hg38_pos_id": hg38_id,
                        "hg19_pos_id": hg19_id,
                        "aliases": {
                            "create": alias_create
                        } if alias_create else None,
                    },
                    "update" : {},
                }
            )
        except PrismaError as e:
            print(f"No record created: {e}")
            continue

        for disease_name in info.get("diseases"):
            if not disease_name:
                continue
            disease_rec = await db.disease.find_first(where={"disease": disease_name})
            if not disease_rec:
                try:
                    disease_rec = await db.disease.create(data={"disease": disease_name})
                except PrismaError:
                    continue
            if not disease_rec:
                continue

            try:
                await db.genedisease.create(data={"gene_id": hgnc, "disease_id": disease_rec.id})
            except PrismaError:
                pass


async def main(output_file) -> None:
    db = Prisma()
    await db.connect()

    # Do the work here
    genes = fetch_pubmed_annotations("38790019")
    await save_genes_to_db(db, genes)

    def set_default(obj):
        if isinstance(obj, set):
            return list(obj)
        raise TypeError
    
    pretty_genes = json.dumps(genes, indent=4, default=set_default)
    # print(pretty_genes)
    with open(output_file, "w") as f:
        print(pretty_genes, file=f)

    await db.disconnect()

if __name__ == "__main__":
    # Potential input arguments
    parser = argparse.ArgumentParser(description="PMID gene extractor script")
    parser.add_argument('--output', '-o', default="output.json", help="Specify an output file")
    args = parser.parse_args()
    if args.output:
        print(f"Output file: {args.output}")

    asyncio.run(main(args.output))