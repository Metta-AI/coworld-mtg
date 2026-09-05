import support as r
import pathlib,json,re,tarfile,hashlib
r.OUT=pathlib.Path(__file__).resolve().parent

def check_counts(record,n,ignored):
    assert len(record['test_results'])==1
    m=re.search(r'(\d+) passed; (\d+) failed; (\d+) ignored;',record['test_results'][0]);assert m
    p,f,i=map(int,m.groups());assert p+f==n and i==ignored
    assert record['exit']==(101 if f else 0)
    return {'passed':p,'failed':f,'ignored':i}

def inspect(directory,mutant=False):
    receipt=json.loads((directory/'receipt.json').read_text());manifest=json.loads((directory/'source.json').read_text())
    changes=[p for p in r.MANIFEST if manifest[p]!=r.MANIFEST[p]]
    if mutant:
        spec=json.loads((r.OUT/receipt['id']/'mutation.json').read_text());assert changes==[spec['row']['file']]
        assert r.sha(r.OUT/receipt['id']/'mutation.patch')==spec['patch_sha256']
    else:assert not changes
    with tarfile.open(directory/'source.tar.gz','r:gz') as tar:
        actual={m.name:hashlib.sha256(tar.extractfile(m).read()).hexdigest() for m in tar.getmembers() if m.isfile()}
    assert actual==manifest
    binding=receipt['binary_binding'];assert r.sha(binding['path'])==binding['sha256']
    assert r.sha(binding['cargo_command_receipt'])==binding['cargo_command_receipt_sha256']
    if mutant or receipt['phase']=='baseline':
        assert binding['source_manifest_sha256']==r.sha(directory/'source.json')
        assert binding['fresh_engine_artifacts']
        assert binding['compiler_artifact']['artifact']['fresh'] is False
        for a in binding['fresh_engine_artifacts']:assert any(f['newer_than_command_start'] for f in a['hashed_files'])
    else:
        assert binding['source_manifest_sha256']==r.sha(directory/'source.json')
        assert receipt['execution_method'].startswith('reused preserved canonical')
    assert receipt['fmt']['exit']==0 and r.sha(receipt['fmt']['log'])==receipt['fmt']['log_sha256']
    commands=[]
    for i,record in enumerate(receipt['results']):
        assert record['source_verified_after'];assert r.sha(record['log'])==record['log_sha256']
        if record['argv'][0]!='cargo':
            context=json.loads((r.OUT/'runtime-context.json').read_text());assert record['cwd']==context['actual_cwd'];assert record['env']==context['allowlisted_environment'];assert record['runtime_context_sha256']==r.sha(r.OUT/'runtime-context.json')
        c=check_counts(record,184 if i==0 else 1,20 if i==0 else 0)
        txt=pathlib.Path(record['log']).read_text();lines=txt.splitlines();failures=[]
        for j,line in enumerate(lines):
            if 'panicked at ' in line:failures.append('\n'.join(lines[j:j+8]))
        if record['exit']==101:assert failures and 'assertion' in txt
        if not mutant:assert record['exit']==0
        commands.append({'argv':record['argv'],'counts':c,'exit':record['exit'],'log':record['log'],'log_sha256':record['log_sha256'],'failure_contexts':failures})
    return {'directory':str(directory),'phase':receipt['phase'],'source_manifest_sha256':r.sha(directory/'source.json'),'source_archive_sha256':r.sha(directory/'source.tar.gz'),'receipt_sha256':r.sha(directory/'receipt.json'),'execution_method':receipt['execution_method'],'binary_sha256':binding['sha256'],'binary_binding':binding,'commands':commands}

def main():
    assert (r.OUT/'canonical.exit').read_text().strip()=='0'
    assert (r.OUT/'mutations.exit').read_text().strip()=='0'
    complete=json.loads((r.OUT/'two-complete.json').read_text());assert len(complete['rows'])==2 and complete['all_discriminated']
    baseline=inspect(r.OUT/'canonical-runtime-confirmed');rows=[];config=json.loads((r.OUT/'case-map.json').read_text())
    inputs=json.loads((r.OUT/'build-inputs.json').read_text());assert r.sha(r.OUT/'generated-build-outputs.tar.gz')==inputs['generated_archive_sha256']
    for group in ['compiler_tools','generated_outputs']:
        for path,record in inputs[group].items():assert r.sha(path)==record['sha256']
    with tarfile.open(r.OUT/'generated-build-outputs.tar.gz','r:gz') as tar:
        generated={str(r.ROOT/m.name):hashlib.sha256(tar.extractfile(m).read()).hexdigest() for m in tar.getmembers() if m.isfile()}
    assert generated=={path:record['sha256'] for path,record in inputs['generated_outputs'].items()}
    for result in complete['rows']:
        assert result['complete_discrimination'] and len(result['designated'])==2
        assert all(x['exit']==101 and x['reached_assertion'] for x in result['designated'])
        assert all(x['exit']==0 for x in result['controls'])
        row={'result':result,'mutation':json.loads((r.OUT/result['id']/'mutation.json').read_text()),'phases':[],'observations':[]}
        assert row['mutation']['driver_sha256']==r.sha(r.OUT/'mutations.py')
        for kind in ['before','mutant','restored']:
            phase=inspect(r.OUT/(result['id']+'-runtime-'+kind),kind=='mutant');row['phases'].append(phase)
            receipt=json.loads((pathlib.Path(phase['directory'])/'receipt.json').read_text())
            assert receipt['driver_sha256']==r.sha(r.OUT/'mutations.py') and receipt['case_map_sha256']==r.sha(r.OUT/'case-map.json')
            for key in ['auxiliary_before','auxiliary_after']:
                assert receipt[key]['build_inputs_sha256']==r.sha(r.OUT/'build-inputs.json')
                for group in ['compiler_tools','generated_outputs']:
                    assert {p:v['sha256'] for p,v in receipt[key]['observed'][group].items()}=={p:v['sha256'] for p,v in inputs[group].items()}
        restoration=json.loads((r.OUT/result['id']/'restoration.json').read_text());assert restoration['fresh_mtime'] and restoration['all2051_verified'] and not restoration['unexpected_other_restores'];assert restoration['restored_mtime_ns']>restoration['mutated_mtime_ns'];row['restoration']=restoration
        for record in result['designated']:
            text=pathlib.Path(record['log']).read_text();lines=text.splitlines();events=[]
            for line in lines:
                for prefix in ['BATCH_CONTEXT_EVIDENCE ','BATCH_AMBIGUOUS_DEPARTURES ','BATCH_SELF_ARRIVAL_DEPARTURES ']:
                    if prefix in line:events.append({'kind':prefix.strip(),'value':json.loads(line.split(prefix,1)[1])})
            assert any(e['kind']=='BATCH_CONTEXT_EVIDENCE' for e in events)
            failures=[]
            for i,line in enumerate(lines):
                if 'panicked at ' in line:failures.append('\n'.join(lines[i:i+8]))
            assert failures
            assert ('batched eligible subject count' if result['id']=='batched-adapter' else 'one natural observer registration for the eligible batch') in failures[0]
            row['observations'].append({'name':record['name'],'log_sha256':record['log_sha256'],'printed_before_failure':events,'first_failure':failures[0],'not_observed':'Assertions and settled payoff after the first failure were not reached; no downstream value claimed.'})
        rows.append(row)
    r.verify(r.MANIFEST)
    runtime=json.loads((r.OUT/'runtime-context.json').read_text());assert all(r.sha(path)==v['sha256'] for path,v in runtime['dynamic_libraries'].items())
    previous={'five_report':'fbde011009235c775433f31015ba76359dd1097cfebf820861a854c36776629d','nine_report':'febe717410490c50cd54fcb10baf5fe2db073c061ee451e3b29be2b63004c78f'}
    assert r.sha(r.OUT.parent/'hushbringer-v9-r2-r3-mutations.md')==previous['five_report']
    assert r.sha(r.OUT.parent/'hushbringer-v9-matcher-mutations.md')==previous['nine_report']
    prior_integrity=[]
    for directory,expected in [('hushbringer-v9-r2-r3-mutations','2c5c6e0764f4168fcb6f1e36752d11ded4acca56798aa98b931adb06e9b37462'),('hushbringer-v9-matcher-mutations','3285adb25a348cad78ef03286c607e2e18a1b5f01eab2ff9ececaaa8e6fd61de')]:
        directory=r.OUT.parent/directory;assert r.sha(directory/'manifest.json')==expected
        files=json.loads((directory/'manifest.json').read_text());assert all(r.sha(directory/path)==value for path,value in files.items())
        prior_integrity.append({'directory':str(directory),'manifest_sha256':expected,'all_files_unchanged':True,'count':len(files)})
    r.save(r.OUT/'prior-artifacts-integrity.json',{'utc':r.utc(),'prior':prior_integrity})
    data={'utc':r.utc(),'canonical':baseline,'rows':rows,'full_source_restored':True,'prior_reports_unchanged':previous,'repair_approval':False,'unresolved':[]};r.save(r.OUT/'audited-results.json',data)
    lines=['# V10 exact batched mutation evidence','', 'Both remaining assigned batched seams discriminated in both independently run orders. Every named control passed. All source bytes are restored to the exact released v10 candidate. This report is bounded verification evidence, not repair approval.','',
    'All edits, builds and tests ran on EC2 in `/home/ubuntu/repos/phase-hushbringer-mutations-r2-r3` with its own target, nightly-2026-04-19 and CARGO_BUILD_JOBS=2. No active Phase or Coworld source write, child executor, commit or push was performed. Prior five-seam and nine-row reports/artifacts remain separate.','',
    f'Released complete2051-source manifest `{r.sha(r.FROZEN/"source.json")}`, archive `{r.sha(r.FROZEN/"source.tar.gz")}`, receipt `{r.sha(r.FROZEN/"receipt.json")}`. Exact20-name batch map `{r.sha(r.FROZEN/"batch-test-map.json")}`. All archive member hashes were verified before fresh-mtime adoption; adoption.json records complete post-write verification. The full v10 plan and clean review were read; source-review-notes.md records exact fixture/guard/storage inspection.','',
    '## Compilation and runtime identity','',
    'A new canonical Cargo compilation rebuilt the engine and integration artifacts from the full v10 source, with fresh=false and output mtimes after command start. It passed184 tests with20 existing ignored diagnostics. The actual Cargo integration child supplied package cwd, allowlisted runtime/config/package environment including RUST_MIN_STACK and LD_LIBRARY_PATH, plus executable identity. Its preserved executable then directly passed the same184/20 matrix and23 exact filters before mutations.','',
    f'Canonical executable SHA `{baseline["binary_sha256"]}`. Runtime context SHA `{r.sha(r.OUT/"runtime-context.json")}`; runtime input manifest SHA `{r.sha(r.OUT/"runtime-inputs.json")}`. Compiler tool hashes/versions were recorded before canonical compilation and checked afterward. Generated build-script outputs were archived and hashed immediately after canonical compilation before mutations. Every mutation phase verifies these source/build/runtime inputs; the final audit verifies those outputs, tools and dynamic libraries again. Main-executor card-data generation receipts are retained in the frozen handoff; this executor does not claim an independent generation run.','',
    'Each mutant separately recompiles and runs the entire unchanged184-test matrix, preserves the actual compiled executable, then runs every assigned exact order/control filter on that preserved mutant binary. Before/restored checks directly reuse the applicable canonical binary after full2051 source/runtime verification; no restoration compilation is claimed. Exact candidate bytes are written with explicit fresh os.utime before restoration checks. Each recorded phase command has cwd/target/flags, source checks, log/exit and executable hash records. Mutations are formatted before snapshots and recorded phase commands run fmt --all --check. No tests, expectations, setup or guard order were altered.','',
    '## Results','', '| Exact seam | Mutant full matrix pass/fail/ignored | Designated exact failures | Named exact controls passed | Before/restored matrix |','|---|---|---|---|---|']
    for row in rows:
        result=row['result'];c=result['matrix_counts'];lines.append(f'| {result["id"]} | {c["passed"]}/{c["failed"]}/{c["ignored"]} | {len(result["designated"])} | {len(result["controls"])} |184 pass /20 ignored|')
    for row in rows:
        m=row['mutation'];lines += ['',f'### {row["result"]["id"]}','',f'Production `{m["row"]["file"]}` in `matching_batched_trigger_events`. Exact patch SHA `{m["patch_sha256"]}`; mutant file SHA `{m["mutant_sha256"]}`. The ordinary precondition and the other batched seam remain unchanged.','']
        for phase in row['phases']:
            lines += [f'{phase["phase"]}: {phase["execution_method"]}; source manifest `{phase["source_manifest_sha256"]}`; source archive `{phase["source_archive_sha256"]}`; executable `{phase["binary_sha256"]}`; phase receipt `{phase["receipt_sha256"]}`.','']
        for observation in row['observations']:
            lines += [f'Independently run `{observation["name"]}`; log SHA `{observation["log_sha256"]}`.','```text',observation['first_failure'],'```','']
        lines += ['Independently passing mutant controls:','']
        for control in row['result']['controls']:lines.append(f'- `{control["name"]}`: exit0; log SHA `{control["log_sha256"]}`.')
    lines += ['', '## Interpretation and handoff','',
    'For the adapter seam, the mixed creature/noncreature fixture reaches the inner batch helper through the eligible noncreature seed. Its native departure/snapshot/peer/incarnation guards run first. Both designated orders print the actual natural trigger/batch context before failing the eligible subject count assertion. The unchanged exact subject-list and settled +11 payoff assertions after that count failure are not claimed reached. No-Hush and single-subject controls execute independently.','',
    'For the broad batched death gate, the destination-functioning Any/SelfRef seed reaches the inner helper with Hush surviving. Both designated orders print the actual natural context before failing the registration-count assertion. Subsequent subject and settled-payoff values are not claimed observed. Explicit-Battlefield and no-Hush controls, plus original nonbatched compatibility tests, execute independently. The source helper correctly expects None subject_match_count for this self trigger.','',
    'Complete printed native departure/context payloads, first failures, all before/mutant/restored command results and binary/source associations are in audited-results.json and the retained logs. Full-matrix failures are reported separately from the designated semantic failures; no zero-match, setup/compile error, ignored diagnostic or unexecuted later assertion counts as discrimination.','',
    'Both exact held mutations are completed and ownership is released. No unresolved item remains in this bounded two-seam assignment. The isolated checkout contains the exact v10 candidate bytes. Overall implementation approval, final validation, commit/push and Coworld attribution remain with root and its independent reviewers.','']
    report=r.OUT.parent/'hushbringer-v10-batched-mutations.md';report.write_text('\n'.join(lines))
    manifest={str(p.relative_to(r.OUT)):r.sha(p) for p in sorted(r.OUT.rglob('*')) if p.is_file() and p not in [r.OUT/'manifest.json',r.OUT/'receipt.json'] and '__pycache__' not in p.parts};r.save(r.OUT/'manifest.json',manifest)
    receipt={'utc':r.utc(),'report':str(report),'report_sha256':r.sha(report),'manifest_sha256':r.sha(r.OUT/'manifest.json'),'audit_sha256':r.sha(r.OUT/'audited-results.json'),'completed_exact_seams':2,'designated_order_failures':4,'named_controls_passed':sum(len(row['result']['controls']) for row in rows),'canonical_full_matrix':{'passed':184,'ignored':20},'all2051_source_restored':True,'ownership_released':True,'repair_approval':False,'unresolved':[]};r.save(r.OUT/'receipt.json',receipt);print(json.dumps(receipt,indent=2));print('RECEIPT_SHA256',r.sha(r.OUT/'receipt.json'))
if __name__=='__main__':main()
