from pathlib import Path
from urllib.request import urlretrieve
import zipfile, hashlib, json

out = Path('/home/ubuntu/jobs/626368693de4_a2')
url = 'https://tandf.figshare.com/ndownloader/articles/1132662/versions/1'
archive = out/'neyriz_figshare_1132662_v1.zip'
urlretrieve(url, archive)
print('archive', archive, archive.stat().st_size, hashlib.md5(archive.read_bytes()).hexdigest())
with zipfile.ZipFile(archive) as z:
    for item in z.infolist():
        print(item.filename, item.file_size)
    z.extractall(out/'neyriz_figshare_1132662_v1')
print('extracted', out/'neyriz_figshare_1132662_v1')

# Inspect Excel workbooks for sheet names, dimensions, headers, coordinate-like fields.
import pandas as pd
folder = out/'neyriz_figshare_1132662_v1'
for fp in sorted(folder.glob('*.xls*')):
    print('\nWORKBOOK', fp.name)
    x = pd.ExcelFile(fp)
    print('SHEETS', x.sheet_names)
    for s in x.sheet_names:
        raw = pd.read_excel(fp, sheet_name=s, header=None)
        print('SHEET',repr(s),'shape',raw.shape)
        print(raw.iloc[:12,:min(15,raw.shape[1])].to_string(index=False,header=False))
        ss = raw.astype(str).apply(lambda col: col.str.contains('lat|lon|long|coord|location|UTM|Easting|Northing', case=False, regex=True, na=False)).any()
        found = [str(k) for k,v in ss.items() if v]
        if found: print('COORD_KEYWORD_COLUMNS',found)
# extract docx text via zip XML quick grep
from zipfile import ZipFile
from xml.etree import ElementTree as ET
for fp in folder.glob('*.docx'):
    with ZipFile(fp) as z:
        xml=z.read('word/document.xml')
    root=ET.fromstring(xml)
    text=' '.join(t.text or '' for t in root.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'))
    (out/'figshare_docx_text.txt').write_text(text,encoding='utf-8')
    print('\nDOCX',fp.name, 'text:',text[:5000])
    for term in ['latitude','longitude','coordinates','UTM','location']:
        print(term, text.lower().find(term))
