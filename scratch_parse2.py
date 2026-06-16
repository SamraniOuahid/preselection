import docx
from docx.document import Document
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import Table
from docx.text.paragraph import Paragraph

def iter_block_items(parent):
    if isinstance(parent, Document):
        parent_elm = parent.element.body
    elif isinstance(parent, docx.table._Cell):
        parent_elm = parent._tc
    else:
        raise ValueError("Something's not right")

    for child in parent_elm.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, parent)
        elif isinstance(child, CT_Tbl):
            yield Table(child, parent)

doc_path = "/home/ouahid/myproject/stage/preseclection/rapport/Rapport_EST_Fes_FINAL_NOIR.docx"
doc = docx.Document(doc_path)
for i, block in enumerate(list(iter_block_items(doc))[:20]):
    if isinstance(block, Paragraph):
        print(f"[{i}] Paragraph ({block.style.name}): {block.text[:50]}")
    elif isinstance(block, Table):
        print(f"[{i}] Table with {len(block.rows)} rows")
