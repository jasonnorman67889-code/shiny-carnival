from pathlib import Path
import re

p = Path(r"c:\Users\HomePC\OneDrive\cookies-sec\PHASE4_IMPLEMENTATION.md")
lines = p.read_text(encoding='utf-8').splitlines()
out = []

list_re = re.compile(r"^\s*([-*+] |\d+\. )")
i = 0
while i < len(lines):
    line = lines[i]
    if list_re.match(line):
        # if previous line not blank, insert blank
        if len(out) > 0 and out[-1].strip() != "" and not list_re.match(out[-1]):
            out.append("")
        # append consecutive list lines
        while i < len(lines) and list_re.match(lines[i]):
            out.append(lines[i])
            i += 1
        # ensure a blank line after the list block
        if i < len(lines) and lines[i].strip() != "":
            out.append("")
        continue
    else:
        out.append(line)
        i += 1

# Normalize table pipes: ensure spaces around cell content for lines starting with '|'
for idx, line in enumerate(out):
    if line.strip().startswith('|'):
        # split and strip spaces, then rejoin with single spaces
        cells = line.split('|')
        # keep leading and trailing pipes
        new_cells = ['']
        for cell in cells[1:-1]:
            new_cells.append(' ' + cell.strip() + ' ')
        new_cells.append('')
        out[idx] = '|'.join(new_cells)

p.write_text('\n'.join(out) + '\n', encoding='utf-8')
print('autofix: applied list and table spacing fixes')
