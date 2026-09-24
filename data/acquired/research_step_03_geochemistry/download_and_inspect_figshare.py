from pathlib import Path
from urllib.request import urlretrieve
import zipfile, hashlib
import pandas as pd

out = Path('/home/ubuntu/jobs/626368693de4_a2/figshare_files')
out.mkdir(exist_ok=True)
files = [
 ('tigr_a_942391_sm7054.xls', 'https://ndownloader.figshare.com/files/1628043', '162ad2327f20c39e77e5019854e0b618'),
 ('tigr_a_942391_sm7047.xlsx','https://ndownloader.figshare.com/files/1628044','d005899975f46aece57ec0a62d91be58'),
 ('tigr_a_942391_sm7044.xls','https://ndownloader.figshare.com/files/1628045','d566e04bd34df071540c3199170fd2bd'),
 ('tigr_a_942391_sm7039.xls','https://ndownloader.figshare.com/files/1628046','1b89e48068f1583906177874df66ddc8'),
 ('tigr_a_942391_sm7036.xls','https://ndownloader.figshare.com/files/1628047','0fffb2ab83d4273df9b5e1ad7da08478'),
 ('tigr_a_942391_sm7028.docx','https://ndownloader.figshare.com/files/1628048','2f2126fac1252ee5378c0100b5b2d18f'),
]
for fn, url, expected in files:
  fp=out/fn
  urlretrieve(url,fp)
  got=hashlib.md5(fp.read_bytes()).hexdigest()
  print('FILE',fn,'bytes',fp.stat().st_size,'md5',got,'expected',expected,'OK',got==expected)

for fp in sorted(out.glob('*.xls*')):
  print('\nWORKBOOK',fp.name)
  x=pd.ExcelFile(fp)
  print('SHEETS',x.sheet_names)
  for sh in x.sheet_names:
    raw=pd.read_excel(fp,sheet_name=sh,header=None)
    print('SHEET',repr(sh),'shape',raw.shape)
    print(raw.iloc[:16,:min(raw.shape[1],16)].to_string(index=False,header=False))
    keywords=' '.join(raw.fillna('').astype(str).head(20).values.flatten()).lower()
    print('LOCATION_TERM_IN_HEADER_ROWS',any(k in keywords for k in ['latitude','longitude','coordinate','location','easting','northing','utm']))

fp=out/'tigr_a_942391_sm7028.docx'
with zipfile.ZipFile(fp) as z: xml=z.read('word/document.xml')
from xml.etree import ElementTree as ET
root=ET.fromstring(xml)
text=' '.join(t.text or '' for t in root.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'))
(out/'docx_plaintext.txt').write_text(text,encoding='utf-8')
print('\nDOCX_TEXT',text[:10000])
print('DOCX_COORDINATE_TERMS',{k:text.lower().count(k) for k in ['latitude','longitude','coordinate','location','utm','easting','northing']})
