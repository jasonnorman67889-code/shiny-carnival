import re
from pathlib import Path

p = Path(r"c:\Users\HomePC\OneDrive\cookies-sec\PHASE4_IMPLEMENTATION.md")
text = p.read_text(encoding="utf-8")
lines = text.splitlines()

issues = []

# MD022: headings should be surrounded by blank lines (check blank before heading)
in_fence = False
for i, line in enumerate(lines):
    if re.match(r"^(```+)", line):
        in_fence = not in_fence
        continue
    if in_fence:
        continue
    if re.match(r"^#{1,6} ", line):
        if i > 0 and lines[i-1].strip() != "":
            issues.append(("MD022", i+1, line.strip()))

# MD032: lists should be surrounded by blank lines (check blank before list)
in_fence = False
for i, line in enumerate(lines):
    if re.match(r"^(```+)", line):
        in_fence = not in_fence
        continue
    if in_fence:
        continue
    if re.match(r"^([-*+] |\d+\. )", line):
        # only flag if previous line is not blank and not part of a list
        if i > 0 and lines[i-1].strip() != "" and not re.match(r"^([-*+] |\d+\. )", lines[i-1]):
            issues.append(("MD032", i+1, line.strip()))

# Fenced blocks detection
fence_open = None
for i, line in enumerate(lines):
    m = re.match(r"^(```+)(.*)$", line)
    if m:
        fence = m.group(1)
        lang = m.group(2).strip()
        if fence_open is None:
            # opening fence
            fence_open = (i, fence, lang)
            # MD040: fenced code blocks should have a language specified
            if lang == "":
                issues.append(("MD040", i+1, "Missing fence language"))
            # MD031: fenced code blocks should be surrounded by blank lines (before)
            if i > 0 and lines[i-1].strip() != "":
                issues.append(("MD031", i+1, "Missing blank line before fence"))
        else:
            # closing fence
            start_i, _, _ = fence_open
            # check closing fence spacing after
            if i+1 < len(lines) and lines[i+1].strip() != "":
                issues.append(("MD031", i+1, "Missing blank line after fence"))
            fence_open = None

# MD034: bare URLs
url_pattern = re.compile(r"https?://[\w\-._~:/?#\[\]@!$&'()*+,;=%]+")
for i, line in enumerate(lines):
    for m in url_pattern.finditer(line):
        url = m.group(0)
        # refine: don't include a trailing ')' in the URL match
        if url.endswith(')'):
            url = url[:-1]
        # if url inside markdown link [text](url) or <url>, skip
        if re.search(r"\]\(" + re.escape(url) + r"\)", line):
            continue
        if re.search(r"<" + re.escape(url) + r">", line):
            continue
        issues.append(("MD034", i+1, url))

# MD060: basic table pipe spacing check (space after and before pipes)
in_table = False
for i, line in enumerate(lines):
    if re.match(r"^\|", line):
        # check for pipes without surrounding spaces (avoid header separator like |---|)
        cells = line.split('|')
        for idx, cell in enumerate(cells[1:-1], start=1):
            # cell should start with a space and end with a space
            if not cell.startswith(' '):
                issues.append(("MD060", i+1, f"Missing space after pipe in cell {idx}"))
            if not cell.endswith(' '):
                issues.append(("MD060", i+1, f"Missing space before next pipe in cell {idx}"))

# Print results
if not issues:
    print("OK: No issues found by quick verifier")
else:
    for code, line_no, msg in issues:
        print(f"{code}: Line {line_no}: {msg}")
    print(f"\nTotal issues: {len(issues)}")
