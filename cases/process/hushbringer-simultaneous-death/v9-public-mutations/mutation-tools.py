"""Pure source transforms and durable commands for isolated mutation work.
No code here edits the active checkout. Execution requires an explicit checkout.
"""
from pathlib import Path
import re,subprocess,hashlib,json,datetime,os,tarfile,difflib

def balanced_end(text,start,opener='(',closer=')'):
    assert text[start]==opener
    depth=1;i=start+1
    in_string=False;escape=False;line_comment=False;block_depth=0
    while depth:
        c=text[i];n=text[i:i+2]
        if line_comment:
            if c=='\n':line_comment=False
        elif block_depth:
            if n=='/*':block_depth+=1;i+=1
            elif n=='*/':block_depth-=1;i+=1
        elif in_string:
            if escape:escape=False
            elif c=='\\':escape=True
            elif c=='"':in_string=False
        elif n=='//':line_comment=True;i+=1
        elif n=='/*':block_depth=1;i+=1
        elif c=='"':in_string=True
        elif c==opener:depth+=1
        elif c==closer:depth-=1
        i+=1
    return i

def function_span(text,name):
    m=re.search(r'\bfn '+re.escape(name)+r'\s*(?:<[^{}]*>)?\s*\(',text)
    assert m,name
    start=m.start()
    opening=text.index('{',m.end())
    return start,balanced_end(text,opening,'{','}')

def unwrap_call(text,marker,index=0):
    matches=list(re.finditer(re.escape(marker)+r'\s*\(',text))
    assert len(matches)>index,(marker,index,len(matches))
    m=matches[index];opening=text.index('(',m.start());end=balanced_end(text,opening)
    content=text[opening+1:end-1].rstrip().removesuffix(',').rstrip()
    closure=re.search(r'\|state,\s*events(?:,\s*owner)?\|',content)
    assert closure,(marker,content[:140])
    body=content[closure.end():].strip()
    replacement='(|| '+body+')()'
    return text[:m.start()]+replacement+text[end:]

def replace_exact(text,old,new,count=1):
    assert text.count(old)==count,(old[:120],text.count(old),count)
    return text.replace(old,new)

def transform(text,operations):
    for op in operations:
        name=op.get('function')
        if name:
            a,b=function_span(text,name);region=text[a:b]
        else:a,b=0,len(text);region=text
        if op['kind']=='replace':
            region=replace_exact(region,op['old'],op['new'],op.get('count',1))
        elif op['kind']=='unwrap':
            region=unwrap_call(region,op['marker'],op.get('index',0))
        else:raise ValueError(op['kind'])
        text=text[:a]+region+text[b:]
    return text

def hash_file(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def run_command(checkout,out,command,manifest_files):
    assert checkout.resolve()==Path('/home/ubuntu/repos/phase-hushbringer-mutations')
    assert not (checkout/'target').is_symlink()
    out.mkdir(exist_ok=False)
    env=dict(os.environ,PATH='/home/ubuntu/.cargo/bin:'+os.environ['PATH'],CARGO_BUILD_JOBS='2',
             CARGO_TARGET_DIR=str(checkout/'target'),RTK_DISABLED='1')
    manifest={f:hash_file(checkout/f) for f in manifest_files}
    (out/'source.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (out/'candidate-and-mutation.patch').write_bytes(subprocess.check_output(['git','diff','--binary'],cwd=checkout))
    with tarfile.open(out/'source.tar.gz','w:gz') as archive:
        for f in manifest_files:archive.add(checkout/f,arcname=f,recursive=False)
    receipt={'source_archive_sha256':hash_file(out/'source.tar.gz'),'command':command,'checkout':str(checkout),'target':env['CARGO_TARGET_DIR'],
             'source_manifest_sha256':hash_file(out/'source.json'),
             'started':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    with (out/'command.log').open('wb') as stream:
        result=subprocess.run(command,cwd=checkout,env=env,stdout=stream,stderr=subprocess.STDOUT)
    (out/'command.exit').write_text(str(result.returncode)+'\n')
    artifacts=[]
    for line in (out/'command.log').read_text(errors='replace').splitlines():
        if not line.startswith('{'):continue
        try:msg=json.loads(line)
        except json.JSONDecodeError:continue
        if msg.get('reason')=='compiler-artifact' and 'engine' in msg.get('package_id',''):
            executable=msg.get('executable')
            artifacts.append({'package_id':msg.get('package_id'),'target':msg.get('target'),'fresh':msg.get('fresh'),
                              'executable':executable,'executable_sha256':hash_file(Path(executable)) if executable else None})
    receipt.update(exit=result.returncode,log_sha256=hash_file(out/'command.log'),artifacts=artifacts,
                   changed_during_run=[f for f,h in manifest.items() if hash_file(checkout/f)!=h],
                   finished=datetime.datetime.now(datetime.timezone.utc).isoformat())
    (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return receipt
