import os

dir_path = "/home/ouahid/myproject/stage/preseclection/sections"

for filename in os.listdir(dir_path):
    if filename.endswith(".tex"):
        file_path = os.path.join(dir_path, filename)
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Replace special unicode characters
        content = content.replace("≥", "$\\geq$")
        content = content.replace("Σ", "$\\Sigma$")
        content = content.replace("✓", "OK")
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
            
print("Unicode fixes applied.")
