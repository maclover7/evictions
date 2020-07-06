import pdftotext

def process(pdf):
    from evictions.tasks import CaseImporter
    ci = CaseImporter(None, None, None, None, None, None)

    flatten = lambda l: [item for sublist in l for item in sublist]
    parse_page = lambda p: list(filter(None, flatten([ line.split("                  ") for line in p.split("\n")])))
    docket_text = list(flatten(parse_page(page) for page in pdf))
    new_dd = ci.parse_docket_text(docket_text, None)
    print(new_dd)

with open("/Users/jon/Downloads/MDJReport1.pdf", "rb") as f:
    pdf = pdftotext.PDF(f)
    process(pdf)
