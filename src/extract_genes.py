import asyncio
import argparse
# from prisma import Prisma
import requests
from xml.etree import ElementTree
import json

from api_calls import fetch_pubmed_text, get_annotations
from parse import parse_genes

async def main(output_file, cache) -> None:
    # db = Prisma()
    # await db.connect()

    def write_to_file(fileName, content, is_list):
        print(type(content))
        print(isinstance(content, list))
        with open(fileName, "w") as file:
            if is_list:
                for i in content:
                    file.write(i)
                    file.write("\n")
            else:
                file.write(json.dumps(content, indent=4))
        return

    # Do the work here
    # Fetch the text from the article
    text = []
    if cache:   
        with open("text.txt", "r") as file:
            lines = file.readlines()
            text = [line.strip() for line in lines]
    if not text:
        text = fetch_pubmed_text("38790019")
        write_to_file("text.txt", text, True)

    # Find the annotations from the text
    annotations = {}
    if cache:
        with open("annotations.json", "r") as file:
            annotations = json.load(file)
    if not annotations:
        annotations = get_annotations(text)
        write_to_file("annotations.json", annotations, False)

    # Parse the annotations
    genes = {}
    associated_diseases = {}
    if cache:
        with open("genes.json", "r") as file:
            genes = json.load(file)
        with open("associated_diseases.json", "r") as file:
            associated_diseases = json.load(file)
    if not genes and not associated_diseases:
        genes, associated_diseases = parse_genes(annotations)
        write_to_file("genes.json", genes, False)
        write_to_file("associated_diseases.json", associated_diseases, False)

    # Print the results
    pretty_gene = json.dumps(genes, indent=4)
    print(pretty_gene)
    with open(output_file, "w") as file:
        file.write(pretty_gene)

    # await db.disconnect()

if __name__ == "__main__":
    # Potential input arguments
    parser = argparse.ArgumentParser(description="PMID gene extractor script")
    parser.add_argument('--output', '-o', default="output.json", help="Specify an output file")
    parser.add_argument('--cache', "-c", action="store_true", help="Use if you want to use cached results if available")
    args = parser.parse_args()
    if args.output:
        print(f"Output file: {args.output}")

    asyncio.run(main(args.output, args.cache))