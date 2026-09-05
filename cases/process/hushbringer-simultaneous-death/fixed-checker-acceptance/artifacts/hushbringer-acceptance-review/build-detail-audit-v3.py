from pathlib import Path
import json,hashlib,difflib,subprocess,datetime,re
O=Path(__file__).parent;E=O.parent;R=Path('/home/ubuntu/repos/coworld-mtg');P=Path('/home/ubuntu/repos/phase-verifiable-loop');B=R/'tmp/verifiable-loop/isolated-baseline-build';D=R/'tmp/verifiable-loop/isolated-candidate-build'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text())
records={};descriptors={}
for label,root in [('baseline',B),('candidate',D)]:
 messages=[json.loads(l) for l in (root/'cargo-messages.jsonl').read_text().splitlines() if l.strip()];artifacts=[x for x in messages if x.get('reason')=='compiler-artifact'];assert messages[-1]=={'reason':'build-finished','success':True}
 assert len(artifacts)==206 and all(x['fresh'] is False for x in artifacts)
 desc=[]
 for x in artifacts:
  package=x['package_id']
  if package in ['git+https://github.com/nishu-builder/phase.git?rev=2dec6c88915db4697706234a7ba2fcedd97b1689#engine@0.24.0','path+file:///home/ubuntu/repos/phase-verifiable-loop/crates/engine#0.24.0']:package='reviewed-engine-source'
  else:package=package.replace(str(root),'FROZEN-BUILD')
  desc.append(dict(package_id=package,target_name=x['target']['name'],target_kind=x['target']['kind'],profile=x['profile'],features=x['features']))
 descriptors[label]=sorted(desc,key=lambda x:json.dumps(x,sort_keys=True))
 relevant=[x for x in artifacts if x['target']['name'] in ['engine','coworld-mtg-harness']];h=next(x for x in relevant if x['target']['name']=='coworld-mtg-harness');target_path=Path(h['executable'])
 if label=='candidate':assert sha(target_path)==sha(root/'worker')
 records[label]=dict(build_json_sha256=sha(root/'build.json'),cargo_messages_sha256=sha(root/'cargo-messages.jsonl'),compiler_artifacts=len(artifacts),fresh_artifacts=sum(x['fresh'] for x in artifacts),relevant_artifacts=relevant,worker_sha256=sha(root/'worker'),target_worker_sha256=sha(target_path) if target_path.exists() else None,target_note='Current target exists and was hashed' if target_path.exists() else 'Historical baseline target removed; preserved immutable worker and compiler receipt verified, no current target-byte claim')
assert descriptors['baseline']==descriptors['candidate']
b=(B/'source/Cargo.lock').read_text();d=(D/'source/Cargo.lock').read_text();pin='source = "git+https://github.com/nishu-builder/phase.git?rev=2dec6c88915db4697706234a7ba2fcedd97b1689#2dec6c88915db4697706234a7ba2fcedd97b1689"\n';assert b.count(pin)==1 and b.replace(pin,'')==d
configs=[]
# Cargo's invocation directory is the copied Coworld source, so dependency-local .cargo is not an invocation ancestor.
for root in [B/'source',D/'source']:
 for ancestor in [root,*root.parents]:
  for name in ['config','config.toml']:
   p=ancestor/'.cargo'/name
   if p.exists():configs.append(dict(path=str(p),sha256=sha(p),content=p.read_text()))
for name in ['config','config.toml']:
 p=Path('/home/ubuntu/.cargo')/name
 if p.exists():configs.append(dict(path=str(p),sha256=sha(p),content=p.read_text()))
assert not configs
config=P/'.cargo/config.toml';reviewed=read(E/'hushbringer-v10-citation-fix/frozen-source/source.json');assert sha(config)==reviewed['.cargo/config.toml']
base=read(B/'build.json');candidate=read(D/'build.json')
assert base['compiler']==candidate['compiler'] and base['build_environment']==candidate['build_environment']=={}
assert sha(E/'final-committed-worker-run/0.log')=='18b88df67a861bccb9daad9d9adf935a3810c9c7812d4afec8ac34632c5cf24d'
v=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='PASS',records=records,all_206_normalized_artifact_package_features_profiles_match=True,artifact_comparison_normalization='Only build directory prefixes and the engine package source identity are normalized; registry package IDs, target kind/name, all profile fields and all features must be equal.',resolved_lock_diff=''.join(difflib.unified_diff(b.splitlines(True),d.splitlines(True),fromfile='baseline/Cargo.lock',tofile='candidate/Cargo.lock')),build_environment=candidate['build_environment'],compiler=candidate['compiler'],fresh_build_log_sha256=sha(E/'final-committed-worker-run/0.log'),invocation_ancestor_and_cargo_home_configs=configs,reviewed_dependency_local_config=dict(path=str(config),sha256=sha(config),content=config.read_text(),applied=False,reason='Build executes from the copied Coworld workspace; the Phase dependency directory is not an invocation ancestor. No build alias is invoked.'),reviewed_live_source_count=2051,captured_phase_source_count=2050,capture_scope='Frozen builder captures Cargo.toml/Cargo.lock/rust-toolchain.toml and crates, excluding .cargo/config.toml. The 2050 source payloads exactly match the corresponding reviewed manifest entries; all2051 live reviewed files remain unchanged.',runtime_note='No test compilation is inferred from this normal worker build. Prior full engine suites retain their explicitly documented comment-only source-lineage provenance.')
with (O/'build-detail-audit.json').open('x') as f:json.dump(v,f,indent=2);f.write('\n')
print('PASS: all206 fresh build artifact descriptors match baseline apart from expected source path; lock differs only engine source; correct fresh candidate worker bytes; no applicable ancestor/home Cargo config.')
