from pathlib import Path
import subprocess,hashlib,json,datetime
r=Path('/home/ubuntu/repos/phase-hushbringer-publish');out=Path('/home/ubuntu/coworld-migration-20260904/phase-main-integration-review')
def git(*a):return subprocess.check_output(['git',*a],cwd=r)
def sha(b):return hashlib.sha256(b).hexdigest()
base='2dec6c88915db4697706234a7ba2fcedd97b1689';up='1cf344efe83c871a362bf04e8444e820124c21f8';repair='fa0ebfe88db224ebd32624bb96ef033d338c2d8c'
assert git('merge-base',up,repair).decode().strip()==base
rp=set(git('diff','--name-only',base,repair).decode().splitlines());upp=set(git('diff','--name-only',base,up).decode().splitlines());rows=[]
for path in sorted(rp|upp):
 merged=git('show',':'+path)
 if path not in rp&upp:
  parent=repair if path in rp else up
  assert merged==git('show',parent+':'+path),path
  rows.append({'path':path,'category':'repair_only' if path in rp else 'upstream_only','parent':parent,'sha256':sha(merged)});continue
 original=git('show',repair+':'+path).decode().splitlines(keepends=True);patch=git('diff','--no-color','--unified=3',base,up,'--',path).decode().splitlines(keepends=True);cursor=0;hunks=[];i=0
 while i<len(patch):
  if not patch[i].startswith('@@'):i+=1;continue
  header=patch[i].rstrip();i+=1;old=[];new=[]
  while i<len(patch) and not patch[i].startswith('@@'):
   line=patch[i];i+=1
   if line.startswith('\\'):continue
   assert line[:1] in (' ','-','+'),line
   if line[0] in (' ','-'):old.append(line[1:])
   if line[0] in (' ','+'):new.append(line[1:])
  matches=[p for p in range(cursor,len(original)-len(old)+1) if original[p:p+len(old)]==old]
  assert len(matches)==1,(path,header,matches)
  pos=matches[0];original[pos:pos+len(old)]=new;cursor=pos+len(new);hunks.append({'header':header,'repair_line':pos+1,'unique_exact_context':True})
 assert ''.join(original).encode()==merged,path
 rows.append({'path':path,'category':'overlap','sha256':sha(merged),'patch_sha256':sha(''.join(patch).encode()),'hunks':hunks,'exact_in_memory_reconstruction':True})
mp=Path('/home/ubuntu/coworld-migration-20260904/phase-main-integration/source.json');manifest=json.loads(mp.read_text());tracked=git('ls-files','-z').decode().split('\0')[:-1]
extras=set(tracked)-set(manifest);assert extras=={'.agents/skills','.codex/skills'};assert not set(manifest)-set(tracked)
links={}
for path in extras:
 assert (r/path).is_symlink() and (r/path).is_dir();target=str((r/path).readlink());assert target.encode()==git('show',':'+path);links[path]=target
for path,h in manifest.items():assert sha((r/path).read_bytes())==h,path
assert not git('diff','--name-only');assert not git('ls-files','-u')
index=git('ls-files','--stage');result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'base':base,'upstream':up,'repair':repair,'head':git('rev-parse','HEAD').decode().strip(),'merge_head':git('rev-parse','MERGE_HEAD').decode().strip(),'overlap':sorted(rp&upp),'repair_only':len(rp-upp),'upstream_only':len(upp-rp),'tracked_entries':len(tracked),'source_files':len(manifest),'directory_symlinks':links,'source_manifest_sha256':sha(mp.read_bytes()),'source_matches_manifest':True,'unmerged_index_entries':False,'unstaged_source_changes':False,'index_entries_sha256':sha(index),'files':rows,'setup_note':'Initial assertion assumed the 3257-file manifest included all 3259 tracked entries. Independent check established the two remaining entries are directory symlinks; both were then verified against index blobs. No source mismatch occurred.'}
(out/'independent-preservation-audit.json').write_text(json.dumps(result,indent=2)+'\n');(out/'index-entries.txt').write_bytes(index)
for name,args in [('upstream-integration.patch',('diff','--cached',repair)),('repair-integrated.patch',('diff','--cached',up))]:(out/name).write_bytes(git(*args))
print(json.dumps({k:v for k,v in result.items() if k!='files'},indent=2));print('audit_sha256='+sha((out/'independent-preservation-audit.json').read_bytes()))
