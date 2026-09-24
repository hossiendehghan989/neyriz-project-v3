from pathlib import Path
import pandas as pd
p=Path('figshare_files')
for fp in sorted(p.glob('*.xls*')):
    print('\nFILE:',fp.name)
    for sh in pd.ExcelFile(fp).sheet_names:
        raw=pd.read_excel(fp,sheet_name=sh,header=None)
        title=' | '.join(str(x) for x in raw.iloc[0:3].fillna('').values.flatten() if str(x).strip())[:300]
        coordinate_terms=[]
        for r,c in zip(*raw.astype(str).apply(lambda x:x.str.contains(r'latitude|longitude|\bUTM\b|easting|northing|coordinate',case=False,regex=True,na=False)).to_numpy().nonzero()):
            coordinate_terms.append((int(r),int(c),str(raw.iat[r,c])))
        print('  sheet=',repr(sh),'shape=',raw.shape,'title=',title)
        print('  coord_field_cells=',coordinate_terms[:20])
