import sys, os, zipfile, re
from xml.etree import ElementTree as ET

ROOT = sys.argv[1]

def strip(xmlbytes, tagsep=' '):
    try:
        txt = re.sub(r'<[^>]+>', ' ', xmlbytes.decode('utf-8', 'ignore'))
    except Exception:
        return ''
    txt = re.sub(r'\s+', ' ', txt)
    return txt.strip()

def docx_text(path):
    with zipfile.ZipFile(path) as z:
        if 'word/document.xml' in z.namelist():
            # separar párrafos por </w:p>
            raw = z.read('word/document.xml').decode('utf-8','ignore')
            raw = raw.replace('</w:p>', '\n')
            return re.sub(r'<[^>]+>',' ', raw)
    return ''

def pptx_text(path):
    out=[]
    with zipfile.ZipFile(path) as z:
        slides = sorted([n for n in z.namelist() if re.match(r'ppt/slides/slide\d+\.xml$', n)],
                        key=lambda n: int(re.search(r'(\d+)', n).group(1)))
        for n in slides:
            raw = z.read(n).decode('utf-8','ignore')
            raw = raw.replace('</a:p>','\n')
            t = re.sub(r'<[^>]+>',' ', raw)
            t = re.sub(r'[ \t]+',' ', t).strip()
            if t: out.append(t)
    return out

for dirpath, _, files in os.walk(ROOT):
    for fn in sorted(files):
        p = os.path.join(dirpath, fn)
        rel = os.path.relpath(p, ROOT)
        try:
            if fn.lower().endswith('.docx') and not fn.startswith('~$'):
                t = docx_text(p)
                t = re.sub(r'[ \t]+',' ', t)
                lines = [l.strip() for l in t.split('\n') if l.strip()]
                print(f"\n############ DOCX: {rel} ({len(lines)} párrafos) ############")
                print('\n'.join(lines[:60])[:2500])
            elif fn.lower().endswith('.pptx') and not fn.startswith('~$'):
                sl = pptx_text(p)
                print(f"\n############ PPTX: {rel} ({len(sl)} diapositivas) ############")
                for i, s in enumerate(sl[:12], 1):
                    print(f"  [slide {i}] {s[:180]}")
        except Exception as e:
            print(f"\n############ {rel}: no se pudo leer ({e}) ############")
