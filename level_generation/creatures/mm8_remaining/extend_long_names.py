from pathlib import Path
p=Path(__file__).resolve().parents[1]/'inventory_remaining.py';s=p.read_text()
s=s.replace("re.escape(stem)+r'[a-z]{2}\\d'", "re.escape(stem)+(r'[a-z]+[0-7]' if r['world']=='mm8' else r'[a-z]{2}\\d')")
s=s.replace('For MM7, all_native_family_images','For MM7/MM8, all_native_family_images')
p.write_text(s)
print('MM8 native stored poses include longer native frame names such as m468naa1')
