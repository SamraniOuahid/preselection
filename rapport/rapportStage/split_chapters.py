import os
import re

tex_file = "rapport_EST_Fes.tex"
chapters_dir = "chapitres"

if not os.path.exists(chapters_dir):
    os.makedirs(chapters_dir)

with open(tex_file, "r", encoding="utf-8") as f:
    content = f.read()

# We need to split the document.
# Everything before the first \chapter goes into the preamble part.
# The content is structured exactly with \chapter{...} 

# Split using regex to capture the chapter declaration and the content that follows
parts = re.split(r'(\\chapter\{.*?\})', content)

# parts[0] is everything before the first chapter
preamble_and_frontmatter = parts[0]

# Then we have pairs of (chapter_declaration, chapter_content)
chapters = []
for i in range(1, len(parts)-1, 2):
    chapter_decl = parts[i]
    chapter_body = parts[i+1]
    chapters.append(chapter_decl + chapter_body)

# The last chapter's body might include \end{document}.
# Let's extract \end{document} to keep it in the main file
if "\\end{document}" in chapters[-1]:
    chapters[-1] = chapters[-1].replace("\\end{document}", "")
    end_doc = "\\end{document}"
else:
    end_doc = "\\end{document}" # default fallback

file_names = [
    "01_introduction.tex",
    "02_contexte.tex",
    "03_architecture.tex",
    "04_logique_metier.tex",
    "05_implementation.tex",
    "06_conclusion.tex",
    "07_annexe.tex"
]

new_main_content = preamble_and_frontmatter

for idx, chap_content in enumerate(chapters):
    filename = file_names[idx] if idx < len(file_names) else f"{idx+1}_chapitre.tex"
    filepath = os.path.join(chapters_dir, filename)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(chap_content.strip() + "\n")
    
    # Add input command to main content
    new_main_content += f"\n\\input{{chapitres/{filename}}}\n"

new_main_content += "\n" + end_doc + "\n"

# backup original just in case
os.rename(tex_file, tex_file + ".bak")

with open(tex_file, "w", encoding="utf-8") as f:
    f.write(new_main_content)

print(f"Successfully split {len(chapters)} chapters into {chapters_dir}/")
