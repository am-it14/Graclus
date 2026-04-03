"""Mini reporter: reads the log and writes a clean summary."""
import codecs, re

lines = []
for enc in ("utf-16", "utf-8", "latin-1"):
    try:
        lines = codecs.open('test_output.log', encoding=enc).readlines()
        break
    except FileNotFoundError:
        print("test_output.log not found.")
        lines = []
        break
    except UnicodeDecodeError:
        continue

# Collect tagged lines + key stats
report = []
for l in lines:
    l_s = l.strip()
    if any(tag in l_s for tag in ['[PASS]', '[FAIL]', '[WARN]', 'LAYER', 'DIAGNOSTIC',
                                   'Keys 1-', 'Total students', 'Total clusters',
                                   'Unclustered', 'Edge cases', 'Q1:', 'Q2:', 'Q3:',
                                   'Q4:', 'Q5:', 'Q6:', 'Q7:', 'Q8:', 'Q9:', 'Q10:',
                                   'responses extracted', 'Preview:', 'Key is filename',
                                   'All metadata', 'Model:', 'Embed:', 'All 10 question',
                                   'Clustering output', 'Exception']):
        report.append(l_s)

with open('test_summary.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(report))

print(f"Written {len(report)} lines to test_summary.txt")
