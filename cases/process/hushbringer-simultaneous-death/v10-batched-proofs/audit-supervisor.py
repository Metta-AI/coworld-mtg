from pathlib import Path
import subprocess
p=Path(__file__).resolve().parent
rc=subprocess.call(['python3','-u',str(p/'audit.py')],cwd=p)
(p.parent/'hushbringer-v10-batched-mutations-audit-run.exit').write_text(str(rc)+'\n')
raise SystemExit(rc)
