import os
import re
import docx
from docx.document import Document
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import Table
from docx.text.paragraph import Paragraph

def escape_latex(text):
    text = text.replace('\\', '\\textbackslash ')
    for char in ['%', '_', '&', '#', '$']:
        text = text.replace(char, '\\' + char)
    return text

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
out_dir = "/home/ouahid/myproject/stage/preseclection/sections"
os.makedirs(out_dir, exist_ok=True)

doc = docx.Document(doc_path)

current_file = None
f_out = None
in_list = False

def close_list(f):
    global in_list
    if in_list and f:
        f.write("\\end{itemize}\n\n")
        in_list = False

def switch_file(filename):
    global f_out
    global in_list
    close_list(f_out)
    if f_out:
        f_out.close()
    f_out = open(os.path.join(out_dir, filename), "w", encoding="utf-8")

# Extract text
table_counter = 1
for block in iter_block_items(doc):
    if isinstance(block, Paragraph):
        text = block.text.strip()
        if not text:
            continue
            
        style = block.style.name.lower()
        escaped_text = escape_latex(text)
        
        # Determine if we should start a new file based on Heading 1
        if 'heading 1' in style:
            close_list(f_out)
            if 'remerciement' in text.lower():
                switch_file('remerciements.tex')
                f_out.write("\\chapter*{Remerciements}\n\\addcontentsline{toc}{chapter}{Remerciements}\n\n")
            elif 'résumé' in text.lower() or 'resume' in text.lower() and 'abstract' not in text.lower():
                switch_file('resume.tex')
                f_out.write("\\chapter*{Résumé}\n\\addcontentsline{toc}{chapter}{Résumé}\n\n")
            elif 'abstract' in text.lower():
                switch_file('abstract.tex')
                f_out.write("\\chapter*{Abstract}\n\\addcontentsline{toc}{chapter}{Abstract}\n\n")
            elif 'abréviation' in text.lower() or 'abreviation' in text.lower():
                switch_file('abreviations.tex')
                f_out.write("\\chapter*{Liste des abréviations}\n\\addcontentsline{toc}{chapter}{Liste des abréviations}\n\n")
            elif 'introduction' in text.lower():
                switch_file('introduction.tex')
                f_out.write("\\chapter*{Introduction générale}\n\\addcontentsline{toc}{chapter}{Introduction générale}\n\n")
            elif 'contexte du projet' in text.lower() or 'chapitre 1' in text.lower():
                switch_file('chapitre1.tex')
                title = escaped_text.replace("Chapitre 1 :", "").strip()
                f_out.write(f"\\chapter{{{title}}}\n\n")
            elif 'architecture' in text.lower() or 'chapitre 2' in text.lower():
                switch_file('chapitre2.tex')
                title = escaped_text.replace("Chapitre 2 :", "").strip()
                f_out.write(f"\\chapter{{{title}}}\n\n")
            elif 'logique métier' in text.lower() or 'chapitre 3' in text.lower():
                switch_file('chapitre3.tex')
                title = escaped_text.replace("Chapitre 3 :", "").strip()
                f_out.write(f"\\chapter{{{title}}}\n\n")
            elif 'implémentation' in text.lower() or 'chapitre 4' in text.lower():
                switch_file('chapitre4.tex')
                title = escaped_text.replace("Chapitre 4 :", "").strip()
                f_out.write(f"\\chapter{{{title}}}\n\n")
            elif 'conclusion' in text.lower():
                switch_file('conclusion.tex')
                f_out.write("\\chapter*{Conclusion générale}\n\\addcontentsline{toc}{chapter}{Conclusion générale}\n\n")
            elif 'bibliographie' in text.lower() or 'webographie' in text.lower():
                if f_out and not f_out.name.endswith('bibliographie.tex'):
                    switch_file('bibliographie.tex')
                    f_out.write("\\chapter*{Bibliographie et Webographie}\n\\addcontentsline{toc}{chapter}{Bibliographie et Webographie}\n\n")
            else:
                if f_out:
                    f_out.write(f"\\chapter{{{escaped_text}}}\n\n")
        elif 'heading 2' in style:
            close_list(f_out)
            if f_out:
                # Remove prefix numbering like "1.1 " from the heading
                clean_title = re.sub(r'^\d+\.\d+\s+', '', escaped_text)
                f_out.write(f"\\section{{{clean_title}}}\n\n")
        elif 'heading 3' in style:
            close_list(f_out)
            if f_out:
                # Remove prefix numbering like "1.1.1 "
                clean_title = re.sub(r'^\d+\.\d+\.\d+\s+', '', escaped_text)
                f_out.write(f"\\subsection{{{clean_title}}}\n\n")
        elif 'list paragraph' in style or 'list' in style:
            if not in_list:
                if f_out:
                    f_out.write("\\begin{itemize}\n")
                in_list = True
            if f_out:
                f_out.write(f"\\item {escaped_text}\n")
        else:
            close_list(f_out)
            if f_out:
                if text.startswith('Tableau '):
                    # We will try to handle this as caption later or just bold it.
                    f_out.write(f"\\textbf{{{escaped_text}}}\n\n")
                elif text.startswith('Figure '):
                    f_out.write(f"\\textbf{{{escaped_text}}}\n\n")
                else:
                    f_out.write(f"{escaped_text}\n\n")

    elif isinstance(block, Table):
        close_list(f_out)
        if not f_out:
            continue
        
        # Check if first row is header
        # In a generic way, we count columns
        if len(block.rows) == 0:
            continue
        num_cols = len(block.rows[0].cells)
        col_format = "|" + "|".join(["p{0.15\\textwidth}" for _ in range(num_cols)]) + "|"
        
        f_out.write("\\begin{table}[htbp]\n")
        f_out.write("\\centering\n")
        # Adjust table columns format based on actual counts, to fit page
        f_out.write("\\begin{tabular}{|" + "X|" * num_cols + "}\n" if "tabularx" in col_format else "\\begin{tabular}{|" + "l|" * num_cols + "}\n")
        f_out.write("\\hline\n")
        
        for r_idx, row in enumerate(block.rows):
            cell_texts = []
            for cell in row.cells:
                # Escape and strip newlines inside cells
                c_text = escape_latex(cell.text.replace("\n", " ").strip())
                cell_texts.append(c_text)
            # Some cells might be merged, but `python-docx` duplicates text in merged cells. We can just use a set or output as is.
            # However, docx module returns the same text for merged cells. Let's just output them as they are to avoid losing data,
            # or simplify it.
            # Let's deduplicate text if it spans multiple cells (simplistic approach for merged cells):
            row_line = " & ".join(cell_texts) + " \\\\"
            f_out.write(row_line + "\n")
            f_out.write("\\hline\n")
            
        f_out.write("\\end{tabular}\n")
        f_out.write(f"\\caption{{Tableau {table_counter}}}\n")
        f_out.write(f"\\label{{tab:table_{table_counter}}}\n")
        f_out.write("\\end{table}\n\n")
        table_counter += 1

if f_out:
    close_list(f_out)
    f_out.close()

print("Extraction completed successfully.")
