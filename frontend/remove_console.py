import os
import re

directory = "/home/ouahid/myproject/stage/preseclection/frontend/src"

for root, _, files in os.walk(directory):
    for file in files:
        if file.endswith(".js") or file.endswith(".jsx"):
            file_path = os.path.join(root, file)
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Use regex to comment out console.log, console.error, console.warn
            new_content = re.sub(r'(\s*)console\.(log|error|warn)\(', r'\1// console.\2(', content)
            
            if new_content != content:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                print(f"Updated {file_path}")
