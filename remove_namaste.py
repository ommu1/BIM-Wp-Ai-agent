import pathlib
root = pathlib.Path('.')
count = 0
exts = {'.py', '.md', '.txt', '.json', '.js'}
for p in root.rglob('*'):
    if p.is_file() and p.suffix in exts:
        text = p.read_text(encoding='utf-8', errors='ignore')
        if '🙏' in text:
            p.write_text(text.replace('🙏', ''), encoding='utf-8')
            count += 1
print('files changed:', count)
