import re

with open('rapport_EST_Fes.tex', 'r', encoding='utf-8') as f:
    content = f.read()

def repl(match):
    caption_line = match.group(1)
    header_content = match.group(2)
    
    m = re.search(r'\\caption\{(.*?)\}', caption_line)
    if m:
        title = m.group(1)
        dummy_caption = f"\\caption[]{{{title} (suite)}} \\\\"
    else:
        dummy_caption = caption_line
        
    # Construct the new header
    # firsthead has the real caption
    firsthead = f"{caption_line}\n{header_content}\n\\endfirsthead"
    # head has the dummy caption to avoid lot duplicates
    head = f"{dummy_caption}\n{header_content}\n\\endhead"
    
    return f"{firsthead}\n{head}"

# We look for \caption{...} \\ followed by anything up to \endhead
# We ensure we don't match across tables by excluding \endhead in the .*?
new_content = re.sub(r'(\\caption\{[^{}]*\} \\\\)\n(.*?)\n\\endhead', repl, content, flags=re.DOTALL)

with open('rapport_EST_Fes.tex', 'w', encoding='utf-8') as f:
    f.write(new_content)
print("Done fixing tables.")
