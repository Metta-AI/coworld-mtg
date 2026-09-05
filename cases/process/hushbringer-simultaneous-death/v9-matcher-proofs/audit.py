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
        c=check_counts(record,91 if i==0 else 1,20 if i==0 else 0)
        txt=pathlib.Path(record['log']).read_text();lines=txt.splitlines();failures=[]
        for j,line in enumerate(lines):
            if 'panicked at ' in line:failures.append('\n'.join(lines[j:j+8]))
        if record['exit']==101:assert failures and 'assertion' in txt
        if not mutant:assert record['exit']==0
        commands.append({'argv':record['argv'],'counts':c,'exit':record['exit'],'log':record['log'],'log_sha256':record['log_sha256'],'failure_contexts':failures})
    return {'directory':str(directory),'phase':receipt['phase'],'source_manifest_sha256':r.sha(directory/'source.json'),'source_archive_sha256':r.sha(directory/'source.tar.gz'),'receipt_sha256':r.sha(directory/'receipt.json'),'execution_method':receipt['execution_method'],'binary_sha256':binding['sha256'],'binary_binding':binding,'commands':commands}

def main():
    assert (r.OUT/'supervisor.exit').read_text().strip()=='0'
    complete=json.loads((r.OUT/'nine-complete.json').read_text());assert len(complete['rows'])==9
    baseline=inspect(r.OUT/'canonical-runtime-confirmed');rows=[]
    for result in complete['rows']:
        row={'result':result,'phases':[]}
        for phase in ['before','mutant','restored']:row['phases'].append(inspect(r.OUT/(result['id']+'-runtime-'+phase),phase=='mutant'))
        restore=json.loads((r.OUT/result['id']/'restoration.json').read_text());assert restore['fresh_mtime'] and restore['all2051_verified']
        assert restore['restored_mtime_ns']>restore['mutated_mtime_ns'];row['restoration']=restore
        row['mutation']=json.loads((r.OUT/result['id']/'mutation.json').read_text());rows.append(row)
    r.verify(r.MANIFEST)
    build=json.loads((r.OUT/'build-inputs-verification.json').read_text())
    assert r.sha(r.OUT/'generated-build-outputs.tar.gz')==build['generated_archive_sha256']
    for group in ['compiler_tools','generated_outputs']:
        for path,record in build[group].items():
            assert r.sha(path)==record['sha256']
            assert pathlib.Path(path).stat().st_mtime_ns==record['mtime_ns']
    for path,record in build['source_inputs'].items():assert r.sha(r.ROOT/path)==record['sha256']==r.MANIFEST[path]
    build_final={'utc':r.utc(),'initial_post_build_audit_sha256':r.sha(r.OUT/'build-inputs-verification.json'),'generated_outputs_and_toolchain_hashes_and_mtimes_unchanged':True,'source_build_inputs_verified':True,'timing_note':build['scope']}
    r.save(r.OUT/'build-inputs-final-verification.json',build_final)
    data={'utc':r.utc(),'baseline':baseline,'rows':rows,'held':complete['held'],'all_candidate_bytes_restored':True,'tests_unchanged':True,'repair_approval':False,'build_input_provenance':build_final}
    r.save(r.OUT/'audited-results.json',data);print('AUDIT',len(rows),'rows',flush=True)
    lines=['# Frozen v9 supplemental matcher mutation evidence','',f'Completed nine assigned rows at {r.utc()}. The two batched rows remain unexecuted under root\'s explicit hold for fully reviewed fixture changes. This is bounded verification evidence, not repair approval.','',
    'All work ran on EC2 in `/home/ubuntu/repos/phase-hushbringer-mutations-r2-r3` with its own `target`, nightly-2026-04-19 and CARGO_BUILD_JOBS=2. No Mac build/edit, child executor, commit, push, active Phase write or Coworld repository write. The original five-seam report and artifacts remain separate and unchanged.','',
    'The exact supplemental release SHA is `dee6a9f52c59bf2dd621861ec8e6f7afbedf1465b1eb687776b1683210f52ec4`. Independent ownership verification confirms the original driver skips each reserved marker-only job directory. The complete frozen v9 source manifest is `46ac753dff4229b2b2841a86b5334f2595c4b76bef4be8a4941dd76756f5f803` (2051 files), including cfg(test), new untracked modules and .cargo/config.toml. Full source archives, runtime fixture/card-data/rules manifest/archive, build context, exact mutation patches and commands are retained.','',
    '## Execution method','',
    'Root explicitly authorized preserving a freshly compiled canonical integration executable for candidate-before/restored checks. The canonical full matrix passed 91 tests with 20 existing ignored diagnostics. Every mutant was freshly compiled in the same dedicated target, with Cargo fresh=false engine/integration artifacts and output mtimes after command start; each ran the entire unchanged 91-test matrix and exact named filters. Each mutant executable is also preserved by byte copy and hash.','',
    'After each mutation, the original file bytes were written with fresh mtimes and all 2051 source plus runtime-input hashes were verified. The same full matrix and exact filters then ran directly on the preserved canonical executable. Those restoration checks deliberately reuse the canonical binary; they do not claim a restoration compilation. Candidate-before checks use the same explicit method. Actual Cargo child cwd, allowlisted runtime/config variables including package metadata and LD_LIBRARY_PATH, executable hash and dynamic-library hashes were captured in runtime-context.json; direct commands use that same package cwd/environment and verify library hashes. Source checks bracket every recorded phase command. A supplemental, explicitly later audit of the still-running supervisor records absence of replacement-index/set-gating and library-preload/audit variables; it does not rewrite the earlier Cargo-child capture. Mutations were formatted before snapshots; phase commands use cargo fmt --all --check. No test expectations, public setup or guard ordering were changed.','',
    f'Canonical executable SHA `{baseline["binary_sha256"]}`; canonical full-source archive SHA `{baseline["source_archive_sha256"]}`. Complete Cargo/binary associations are in `runtime-probe/binary.json` and `audited-results.json`; confirmed direct baseline results are in `canonical-runtime-confirmed`.','',
    'Build-inputs-verification.json records a read-only post-build audit of the frozen Cargo.lock, toolchain/config/build-script/TOML source hashes, actual compiler executable hashes, and generated Cargo build outputs. All generated-output mtimes precede the final canonical compilation; output bytes are archived, and final audit rechecks their hashes and unchanged mtimes. The canonical build and every mutant retain Cargo build-script records. This records post-build hashes, not an independent regeneration or a claim they were captured at compilation start.','',
    '## Outcomes','',
    '| Mutation | Mutant matrix pass/fail/ignored | Exact named exits | Restored full matrix |','|---|---|---|---|']
    for row in rows:
        result=row['result'];c=result['matrix_counts'];lines.append(f'| {result["id"]} | {c["passed"]}/{c["failed"]}/{c["ignored"]} | {result["named_exits"]} | 91 pass / 20 ignored |')
    for row in rows:
        m=row['mutation'];assert m['driver_sha256'] in [r.sha(p) for p in r.OUT.glob('*run.py')];lines += ['',f'### {row["result"]["id"]}','',f'Production path `{m["row"]["file"]}`, function(s) '+', '.join('`'+op['function']+'`' for op in m['row']['operations'])+f'. Exact patch SHA `{m["patch_sha256"]}`; mutant file SHA `{m["mutant_sha256"]}`.','',f'Outcome: {row["result"]["outcome"]}.', '']
        for phase in row['phases']:
            lines += [f'{phase["phase"]}: {phase["execution_method"]}; source manifest `{phase["source_manifest_sha256"]}`; archive `{phase["source_archive_sha256"]}`; executable `{phase["binary_sha256"]}`.','']
            for cmd in phase['commands']:
                name=cmd['argv'][1] if not cmd['argv'][0]=='cargo' else 'full matrix'
                lines.append(f'- `{name}`: exit {cmd["exit"]}; {cmd["counts"]}; log SHA `{cmd["log_sha256"]}`.')
            lines.append('')
        mutant=row['phases'][1]
        lines += ['Reached assertion contexts from independently run exact named filters:','']
        for cmd in mutant['commands'][1:]:
            for context in cmd['failure_contexts']:lines += ['```text',context,'```','']
    lines += ['## Interpretation and remaining work','',
    'One preliminary direct-execution setup aborted with stack overflow because the launcher omitted the frozen repository RUST_MIN_STACK=16777216 that Cargo supplies. No mutant had run. Original command/log/exit and successful canonical Cargo91/20 build remain retained; a preliminary stack-corrected full matrix and eleven filters passed, then root required an actual Cargo runtime-identity probe. The recorded package cwd and allowlisted environment/library paths were applied and the full matrix plus eleven exact filters rerun before mutations. The probe itself freshly compiled canonical source and passed91/20; its preserved executable is the final canonical binding. This is setup evidence, not discrimination.','',
    'The first mutant completed designated assertion failures, then the supervisor stopped on a timestamp-bookkeeping check after restoring exact bytes. All2051 hashes were independently verified. The failed supervisor/script are retained; restoration was repeated with an explicit current-time os.utime newer than the mutant, followed by the same full matrix and named filters. Later rows use that robust timestamp check.','',
    'Exact named failures and matrix counts above are observations. The source/control map and pre-execution expectations are in source-review-notes.md. A panic stops its test: later loop cases, peer/counter/snapshot assertions and downstream payoff are not claimed executed. Full-matrix collateral failures are reported separately from designated exact semantic assertions. The ordinary-global-death-gate mutant independently passed clause_local_disjunction_registers_once_for_eligible_sibling while its destination-self-arrival test failed; those are separate executions, not inferred later loop cases. Independently passing named tests and the passing portion of the unchanged full matrix retain controls; no zero-match, data skip, compile failure or ignored desired diagnostic counts as a mutation proof.','',
    'Root holds batched-adapter and batched-global-death-gate. Source review identified that the ordinary guard can mask the current batched-adapter fixture and that the current self-arrival fixture is not batched. The complete v10 plan and clean review have been read; its reviewed mixed creature/noncreature batch/count and batched self-arrival fixtures are being implemented by the separate active executor. Applying that consolidated source requires a new canonical build and separate evidence report. This report does not claim those two mutations ran or that their discrimination is resolved.','',
    'All own-checkout candidate source bytes are restored. Nine-row mutation ownership is released; the two held rows remain assigned but unstarted pending root direction. No repair approval, production pin change, checker change or supported-behavior promotion is made.','']
    report=r.OUT.parent/'hushbringer-v9-matcher-mutations.md';report.write_text('\n'.join(lines))
    manifest={str(p.relative_to(r.OUT)):r.sha(p) for p in sorted(r.OUT.rglob('*')) if p.is_file() and p not in [r.OUT/'manifest.json',r.OUT/'receipt.json'] and '__pycache__' not in p.parts};r.save(r.OUT/'manifest.json',manifest)
    receipt={'utc':r.utc(),'status':'nine exact rows completed; two explicitly held; not repair approval','report':str(report),'report_sha256':r.sha(report),'manifest_sha256':r.sha(r.OUT/'manifest.json'),'audit_sha256':r.sha(r.OUT/'audited-results.json'),'completed':9,'held':complete['held'],'canonical_matrix':{'passed':91,'ignored':20},'all2051_source_restored':True,'ownership_released_for_completed_rows':True,'restored_method':'direct reused preserved candidate executable after complete source/runtime verification'};r.save(r.OUT/'receipt.json',receipt);print(json.dumps(receipt,indent=2));print('RECEIPT_SHA256',r.sha(r.OUT/'receipt.json'))
if __name__=='__main__':main()
