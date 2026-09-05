from pathlib import Path
import json,time,subprocess
out=Path('/home/ubuntu/coworld-migration-20260904/hushbringer-v10-review-fixes')
while True:
 p=out/'card-data-final/receipt.json'
 if p.exists() and 'finished' in json.loads(p.read_text()):break
 time.sleep(5)
r=json.loads(p.read_text());assert r['exit']==0 and r['post_restore_changed']==[]
subprocess.run(['python3',str(out/'freeze-audit.py')],check=True)
subprocess.run(['python3',str(out/'run.py'),str(out/'final-gates.json')],check=True)
