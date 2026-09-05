from pathlib import Path
import json, hashlib, copy, difflib, tarfile, subprocess
from datetime import datetime, timezone

BASE = Path("/home/ubuntu/coworld-migration-20260904")
OLD = BASE / "hushbringer-v10-citation-fix"
NEW = BASE / "hushbringer-v10-map-correction"
REPO = Path("/home/ubuntu/repos/phase-verifiable-loop")
PROOF = BASE / "hushbringer-v9-r2-r3-mutations"
EXPECTED = "ee906941362b78f3ad170fc733a4ca34ee28fcd571f7fafe14f3c900e7204847"
TEST = "crates/engine/tests/integration/trigger_suppression_event_timing.rs"
FILTER = "crates/engine/src/game/filter.rs"
UTC = datetime.now(timezone.utc).isoformat()

def sha(b): return hashlib.sha256(b).hexdigest()
def digest(p): return sha(Path(p).read_bytes())
def ref(p): return {"path": str(p), "sha256": digest(p)}
def read(p): return json.loads(Path(p).read_text())
def dump(v): return json.dumps(v, indent=2) + "\n"
def save(n,v): (NEW/n).write_text(dump(v))
def stable(v): return sha(json.dumps(v,sort_keys=True,separators=(",",":")).encode())
def git(*args): return subprocess.check_output(["git",*args],cwd=REPO,text=True)
def snapshot_sources(manifest):
    actual = {n:digest(REPO/n) for n in manifest}
    assert actual == manifest
    return actual

assert NEW.exists()
assert [p.name for p in NEW.iterdir()] == ["build-package.py"]
old_handoff = read(OLD/"handoff.json")
old_selector = read(OLD/"reviewed-map-selection.json")
old_map = read(OLD/"production-path-maintainer-map.json")
old_manifest = read(OLD/"manifest.json")
old_files = {str(p.relative_to(OLD)):digest(p) for p in OLD.rglob("*") if p.is_file()}
assert all(old_files[n] == h for n,h in old_manifest.items())
assert digest(OLD/"manifest.json") == read(OLD/"seal-receipt.json")["artifact_manifest_sha256"]
source_manifest = read(OLD/"frozen-source/source.json")
assert digest(OLD/"frozen-source/source.json") == EXPECTED
before_source = snapshot_sources(source_manifest)
before_git = {"head":git("rev-parse","HEAD").strip(),"branch":git("branch","--show-current").strip(),"status":git("status","--porcelain=v1","--untracked-files=all")}
assert before_git["head"] == old_handoff["base"]
assert before_git["branch"] == old_handoff["branch"]

freeze = read(OLD/"frozen-source/receipt.json")
archive = Path(freeze["source_archive"])
assert digest(archive) == freeze["source_archive_sha256"]
with tarfile.open(archive) as tf:
    current_archive_files = {m.name:sha(tf.extractfile(m).read()) for m in tf if m.isfile()}
assert current_archive_files == source_manifest

test_bytes = (REPO/TEST).read_bytes()
test_lines = test_bytes.splitlines(keepends=True)
helper_bytes = b"".join(test_lines[4983:5165])
(NEW/"source-route-excerpt.txt").write_text("\n".join(f"{i}: {test_lines[i-1].decode().rstrip()}" for i in range(4984,5166))+"\n")
filter_lines = (REPO/FILTER).read_text().splitlines()
(NEW/"filter-route-excerpt.txt").write_text("\n".join(f"{i}: {filter_lines[i-1]}" for i in range(1440,1512))+"\n")
assert b"StaticDefinition::new(StaticMode::Continuous)" in helper_bytes
assert b"change(specific(entrant), Zone::Battlefield, Zone::Graveyard)" in helper_bytes
assert b"change(specific(grant), Zone::Battlefield, Zone::Exile)" in helper_bytes
assert b"mass_change(specific(entrant), Zone::Graveyard, Zone::Battlefield)" in helper_bytes
assert b"original_entry_lki_public_case(false, true);" in helper_bytes
assert b"original_entry_lki_public_case(true, true);" in helper_bytes
assert b"original_entry_lki_public_case(false, false);" in helper_bytes
assert b"assert_eq!(r.life(P0), 21);" in test_lines[5151]

target_ids = ["R3-original-entry-exit-lki","R3-original-entry-incarnation"]
evidence_audit = []
for rid in target_ids:
    row = next(r for r in old_map["rows"] if r["id"] == rid)
    evidence = row["evidence"][0]
    assert digest(evidence["artifact"]["path"]) == evidence["artifact"]["sha256"]
    assert digest(row["exact_transformation_receipt"]["path"]) == row["exact_transformation_receipt"]["sha256"]
    phases = []
    for phase in evidence["row"]["phases"]:
        folder = PROOF/(rid+"-"+phase["phase"])
        receipt = read(folder/"receipt.json")
        assert digest(folder/"receipt.json") == phase["receipt_sha256"]
        assert digest(folder/"source.json") == phase["source_manifest_sha256"]
        assert digest(folder/"source.tar.gz") == phase["source_archive_sha256"]
        with tarfile.open(folder/"source.tar.gz") as tf:
            archived_test = tf.extractfile(TEST).read()
            archived_filter = tf.extractfile(FILTER).read()
        historical_sources = read(folder/"source.json")
        assert sha(archived_test) == historical_sources[TEST]
        assert sha(archived_filter) == historical_sources[FILTER]
        assert b"".join(archived_test.splitlines(keepends=True)[4983:5165]) == helper_bytes
        checked_tests = []
        for idx,test in enumerate(phase["tests"]):
            log = Path(test["log"])
            assert digest(log) == test["log_sha256"]
            runtime = read(folder/(str(idx)+".receipt.json"))
            assert runtime["argv"] == test["command"]
            assert runtime["exit"] == test["exit"]
            assert runtime["log_sha256"] == test["log_sha256"]
            assert runtime["source_manifest_sha256"] == phase["source_manifest_sha256"]
            assert runtime["test_results"] == test["test_results"]
            text = log.read_text()
            if test["failure_context"]:
                assert test["failure_context"] in text
            if idx == 1 and phase["phase"] == "mutant":
                assert "trigger_suppression_event_timing.rs:5152:5" in text
                assert "  left: 20\n right: 21" in text
            if idx == 1:
                excerpt = text[text.index("\nrunning 1 test\n")+1:]
                (NEW/(rid+"-"+phase["phase"]+"-runtime-excerpt.txt")).write_text(excerpt)
            checked_tests.append({"index":idx,"log":ref(log),"command":ref(folder/(str(idx)+".command.json")),"runtime_receipt":ref(folder/(str(idx)+".receipt.json")),"historical_command":test["command"],"historical_exit":test["exit"],"historical_results":test["test_results"],"new_runtime":False})
        phases.append({"phase":phase["phase"],"receipt":ref(folder/"receipt.json"),"source_manifest":ref(folder/"source.json"),"source_archive":ref(folder/"source.tar.gz"),"historical_test_file_sha256":sha(archived_test),"historical_filter_file_sha256":sha(archived_filter),"helper_lines_4984_5165_identical_to_current":True,"helper_bytes_sha256":sha(helper_bytes),"tests":checked_tests})
    evidence_audit.append({"row_id":rid,"imported_audit":evidence["artifact"],"exact_transformation":row["exact_transformation_receipt"],"historical_evidence_payload_canonical_json_sha256":stable(row["evidence"]),"phases":phases})

route = ("Functioning static +2/+2 is established before a public typed ChangeZone spell moves the 1/1 entrant from Hand to Battlefield as 3/3. "
         "The 2/2 observer's original entry trigger remains unresolved while public ChangeZone responses move the entrant from Battlefield to Graveyard and then exile the static grant from Battlefield. "
         "The original exit LKI is 3/3; the live entrant has reset to 1/1. Resolving the original trigger yields life 21. "
         "The separate no-buff sibling applies the static grant to an unrelated creature, creates no qualifying original entry trigger, and remains at life 20.")
branch = ("After the static-buffed public Hand-to-Battlefield entry, the unresolved original trigger is answered with Battlefield-to-Graveyard ChangeZone, then the grant is exiled before the original trigger resolves. "
          "At original trigger resolution, filter.rs:1489-1501 sees the entrant outside Battlefield, skips the live-object branch, and evaluates the matching cached 3/3 exit LKI against the live 2/2 observer. "
          "The designated public exit-LKI mutant reaches the final life assertion at trigger_suppression_event_timing.rs:5152 and fails with 20 instead of 21.")
reentry_route = ("The same corrected route as R3-original-entry-exit-lki starts with a functioning static +2/+2 grant before public Hand-to-Battlefield entry, leaves the original observer trigger unresolved, "
                 "responds with Battlefield-to-Graveyard ChangeZone, and then exiles the grant from Battlefield. "
                 "Before resolving the original trigger, a public ChangeZoneAll response returns the entrant from Graveyard to Battlefield with the same ObjectId and a different incarnation as 1/1. "
                 "That new 1/1 entry creates no qualifying trigger. The original trigger still compares its original 3/3 exit LKI to the live 2/2 observer and yields life 21.")
reentry_branch = ("Following the corrected static-grant entry, Graveyard departure, and grant-exile route of R3-original-entry-exit-lki, public Graveyard-to-Battlefield ChangeZoneAll returns the same ObjectId as a new 1/1 incarnation before the original trigger resolves. "
                  "At that resolution, filter.rs:1489-1501 sees Battlefield but rejects the new incarnation against the original event's entered_incarnation, so it evaluates the original cached 3/3 exit LKI rather than the new live 1/1. "
                  "The designated public incarnation mutant reaches the final life assertion at trigger_suppression_event_timing.rs:5152 and fails with 20 instead of 21.")
updates = {
 target_ids[0]: {"production_entry":route,"first_reaching_branch":branch},
 target_ids[1]: {"production_entry":reentry_route,"first_reaching_branch":reentry_branch},
}
new_map = copy.deepcopy(old_map)
row_changes = []
for idx,row in enumerate(new_map["rows"]):
    if row["id"] not in updates: continue
    for field,value in updates[row["id"]].items():
        row_changes.append({"json_pointer":f"/rows/{idx}/{field}","row_id":row["id"],"field":field,"old":row[field],"new":value})
        row[field] = value
assert len(row_changes) == 4
assert len(new_map["rows"]) == 67
for old,new in zip(old_map["rows"],new_map["rows"]):
    old_without = {k:v for k,v in old.items() if k not in updates.get(old["id"],{})}
    new_without = {k:v for k,v in new.items() if k not in updates.get(old["id"],{})}
    assert old_without == new_without
    assert old["evidence"] == new["evidence"]
authoritative = {k:str(OLD/v) for k,v in old_selector["authoritative_maps"].items()}
authoritative["maintainer_matrix"] = str(NEW/"production-path-maintainer-map.json")
new_map["authoritative_maps"] = authoritative
new_map["utc"] = UTC
new_map["status"] = "Four factual route-prose fields in two rows corrected; all 67 historical mutation evidence payloads and their original build identities retained. Same frozen source. Ongoing fresh independent full review and final committed-worker acceptance remain pending."
new_map["supersedes"] = {**ref(OLD/"production-path-maintainer-map.json"),"reason":"Only four current route-prose fields corrected in two rows, plus current package timestamp/status/selection references. All historical evidence and source/build identities are unchanged."}
save("production-path-maintainer-map.json",new_map)

# Preserve the full old Markdown rendering and replace only its current header and four field renderings.
old_md = (OLD/"production-path-maintainer-map.md").read_text()
new_md = old_md
for c in row_changes:
    before = json.dumps(c["field"])+": "+json.dumps(c["old"])
    after = json.dumps(c["field"])+": "+json.dumps(c["new"])
    assert new_md.count(before) == 1, (c["json_pointer"],new_md.count(before))
    new_md = new_md.replace(before,after)
old_header = old_md.split("\n",1)[0]
new_header = ("All 67 historical mutation rows are retained below. Four factual route-prose fields in the two R3 original-entry rows are corrected against the unchanged frozen source and original mutation evidence. "
              "All historical evidence payloads and build/source identities remain unchanged. This package ran no compilation or runtime tests. "
              "Use "+str(NEW/"reviewed-map-selection.json")+" for the complete authoritative selection; all other maps remain the unchanged citation-fix artifacts. "
              "Fresh independent full review and final committed-worker acceptance remain pending.")
new_md = new_md.replace(old_header,new_header,1)
(NEW/"production-path-maintainer-map.md").write_text(new_md)

def differences(a,b,p=""):
    if type(a) != type(b): return [{"json_pointer":p,"old":a,"new":b}]
    if isinstance(a,dict):
        out=[]
        for k in sorted(a.keys()|b.keys()):
            q=p+"/"+k.replace("~","~0").replace("/","~1")
            if k not in a or k not in b: out.append({"json_pointer":q,"old":a.get(k),"new":b.get(k)})
            else: out.extend(differences(a[k],b[k],q))
        return out
    if isinstance(a,list):
        assert len(a)==len(b)
        return [r for i,(x,y) in enumerate(zip(a,b)) for r in differences(x,y,p+"/"+str(i))]
    return [] if a==b else [{"json_pointer":p,"old":a,"new":b}]

all_delta = differences(old_map,new_map)
assert len([d for d in all_delta if d["json_pointer"].startswith("/rows/")]) == 4
save("exact-delta.json",{"old_map":ref(OLD/"production-path-maintainer-map.json"),"new_map":ref(NEW/"production-path-maintainer-map.json"),"scope":"Four route-prose fields; current package metadata only outside rows. No source, test or historical evidence edits.","row_changes":row_changes,"complete_json_semantic_delta":all_delta,"unchanged_rows":65,"evidence_payloads_unchanged":67,"markdown_changes":"Original complete rendering retained with only its current header and the same four JSON field renderings replaced."})
patch = "".join(difflib.unified_diff((OLD/"production-path-maintainer-map.json").read_text().splitlines(True),(NEW/"production-path-maintainer-map.json").read_text().splitlines(True),fromfile=str(OLD/"production-path-maintainer-map.json"),tofile=str(NEW/"production-path-maintainer-map.json")))
patch += "".join(difflib.unified_diff(old_md.splitlines(True),new_md.splitlines(True),fromfile=str(OLD/"production-path-maintainer-map.md"),tofile=str(NEW/"production-path-maintainer-map.md")))
(NEW/"exact-delta.patch").write_text(patch)
save("source-evidence-audit.json",{
 "utc":UTC,"source_manifest":ref(OLD/"frozen-source/source.json"),"source_manifest_sha256":EXPECTED,
 "source_archive":ref(archive),"current_source_files_verified":len(source_manifest),"current_archive_members_verified":len(current_archive_files),
 "test_file":ref(REPO/TEST),"filter_file":ref(REPO/FILTER),"source_route_excerpt":ref(NEW/"source-route-excerpt.txt"),"filter_route_excerpt":ref(NEW/"filter-route-excerpt.txt"),
 "helper_source_range":{"first_line":4984,"last_line":5165,"raw_source_bytes_sha256":sha(helper_bytes)},
 "interpretation":[
 "StaticDefinition::Continuous with AddPower/AddToughness 2 is installed before the public entry spell; it is not a temporary pump response.",
 "The actual original-entry response route is Battlefield to Graveyard, then the grant goes Battlefield to Exile; it is not a bounce.",
 "The reentry route additionally uses Graveyard to Battlefield ChangeZoneAll after removing the grant; same ObjectId, different incarnation, 1/1.",
 "Power assertions are explicit; the paired AddPower/AddToughness modifications and 1/1 base establish the corresponding 3/3 and reset 1/1 characteristics.",
 "Historical designated public mutant failures reach line 5152 with 20 versus 21. Later assertions or unrelated fixtures are not inferred from a panic.",
 "The source route excerpt matches all six original phase archives exactly. Runtime and compilation claims retain those historical source/receipt identities."
 ],
 "historical_evidence":evidence_audit,"new_compilation":False,"new_runtime_tests":False,"new_mutations":False,
 "all_67_evidence_payload_checks":[{"row_id":a["id"],"old_canonical_json_sha256":stable(a["evidence"]),"new_canonical_json_sha256":stable(b["evidence"]),"identical":a["evidence"]==b["evidence"]} for a,b in zip(old_map["rows"],new_map["rows"])]
})
bindings = {k:ref(v) for k,v in authoritative.items()}
selector = {
 "utc":UTC,"source_manifest_sha256":EXPECTED,"authoritative_maps":authoritative,"artifact_bindings":bindings,
 "maintainer_markdown":ref(NEW/"production-path-maintainer-map.md"),"supersedes":ref(OLD/"reviewed-map-selection.json"),
 "supersession_scope":"Current selection replaces only the maintainer matrix JSON/Markdown and its factual route prose. Every other selected citation-fix artifact is reused byte-for-byte at its original absolute path. Their embedded relative map references remain historical metadata; this selection is authoritative for current review.",
 "source_changed":False,"tests_changed":False,"historical_evidence_changed":False,"new_compilation":False,"new_runtime_tests":False,"acceptance":False,
 "current_independent_review":"in progress by /root/hushbringer_full_review_final",
 "review_instruction":"Review this full corrected matrix together with the unchanged selected citation-fix maps and unchanged ee906 source archive. No acceptance or new runtime/build result is asserted."
}
save("reviewed-map-selection.json",selector)
save("final-map-consistency-audit.json",{
 "source_manifest_sha256":EXPECTED,"selector":ref(NEW/"reviewed-map-selection.json"),"artifact_bindings":bindings,
 "all_selected_paths_absolute":all(Path(p).is_absolute() for p in authoritative.values()),
 "unchanged_selected_citation_fix_artifacts":8,
 "historical_mutation_rows":67,"classifications":new_map["classifications"],
 "row_text_fields_corrected":4,"rows_corrected":2,"rows_completely_unchanged":65,
 "all_67_historical_evidence_payloads_unchanged":True,
 "all_non_route_row_fields_unchanged":True,
 "counts_retained_from_prior_complete_handoff":old_handoff["production_coverage_map"]["counts"],
 "constructor_count":82,"production_constructors":3,"test_constructors":79,
 "complete_cr_audit_annotations_retained":185,
 "current_source_identity_unchanged":True,"new_runtime_or_compile_claim":False,
 "pending":"Ongoing independent full review and root-owned final committed-worker acceptance."
})
assert snapshot_sources(source_manifest) == before_source
after_git = {"head":git("rev-parse","HEAD").strip(),"branch":git("branch","--show-current").strip(),"status":git("status","--porcelain=v1","--untracked-files=all")}
assert after_git == before_git
after_old_files = {str(p.relative_to(OLD)):digest(p) for p in OLD.rglob("*") if p.is_file()}
assert old_files == after_old_files
save("preservation-audit.json",{
 "utc":datetime.now(timezone.utc).isoformat(),"source_manifest_sha256":EXPECTED,"source_files_before_and_after":2051,
 "all_source_hashes_unchanged":True,"git_state_before_and_after":before_git,"git_state_unchanged":True,
 "prior_package":str(OLD),"prior_package_files":old_files,"prior_package_file_count":len(old_files),"all_prior_package_bytes_unchanged":True,
 "prior_manifest_verified":ref(OLD/"manifest.json"),"prior_seal":ref(OLD/"seal-receipt.json"),
 "scope":"Read-only rehashes of source and historical artifacts. No writes, restoration, builds, runtime tests, commits or pushes in source/proof locations."
})
handoff = {
 "role":"Existing artifact author correcting factual maintainer metadata during an independent full review",
 "status":"Metadata correction sealed for independent review; no source/test change or new implementation round.",
 "utc":UTC,"checkout":str(REPO),"branch":before_git["branch"],"base":before_git["head"],
 "source_manifest_sha256":EXPECTED,"source_freeze":ref(OLD/"frozen-source/receipt.json"),"source_archive":ref(archive),
 "source_changed":False,"tests_changed":False,"source_files_verified":2051,
 "prior_handoff":ref(OLD/"handoff.json"),"prior_handoff_markdown":ref(OLD/"handoff.md"),
 "prior_source_manifest_sha256":old_handoff["prior_source_manifest_sha256"],
 "complete_candidate_diff":old_handoff["diff_summary"]["complete_candidate_diff"],
 "same_source_lineage":ref(OLD/"frozen-source/lineage.json"),
 "factual_correction":{"rows":target_ids,"fields":["production_entry","first_reaching_branch"],"field_count":4,"description":"Static +2/+2 before real public entry, unresolved original trigger, real Battlefield-to-Graveyard ChangeZone response, exile of the grant, and optional Graveyard-to-Battlefield same-ID new-incarnation 1/1. Original exit LKI 3/3 versus observer 2/2; payoff 21, no-buff sibling 20.","exact_delta":ref(NEW/"exact-delta.json"),"full_patch":ref(NEW/"exact-delta.patch")},
 "maintainer_matrix":{"artifact":ref(NEW/"production-path-maintainer-map.json"),"markdown":ref(NEW/"production-path-maintainer-map.md"),"rows":67,"historical_public_mutations":56,"historical_private_mutations":10,"historical_defensive_mutations":1,"historical_evidence_payloads_unchanged":67,"qualification":old_handoff["maintainer_matrix"]["qualification"],"current_independent_verdict":"pending ongoing independent full review"},
 "authoritative_maps":authoritative,"authoritative_map_bindings":bindings,"authoritative_selection":ref(NEW/"reviewed-map-selection.json"),
 "source_and_evidence_verification":ref(NEW/"source-evidence-audit.json"),
 "preservation":ref(NEW/"preservation-audit.json"),"map_consistency":ref(NEW/"final-map-consistency-audit.json"),
 "verification":{"current_round":"Source/archive/hash and exact map-delta verification only. No compilation, runtime tests, generation, mutations or source formatting executed.","unchanged_prior_verification":ref(OLD/"verification-summary.json"),"new_compilation":False,"new_runtime_tests":False,"new_mutations":False,"new_card_generation":False,"new_formatter_execution":False},
 "historical_canonical":ref(OLD/"historical-canonical-reference.json"),
 "parser_gate":old_handoff["parser_gate"],"risks_and_retained_limits":old_handoff["risks_and_retained_limits"],
 "cr_audit":{"artifact":ref(OLD/"cr-audit.json"),"annotation_count":185,"current_round_changes":0,"qualification":"Unchanged citation-fix author audit; independent reviewer controls the current full-review verdict."},
 "reported_metadata_finding":{"status":"corrected by artifact author; awaiting independent review","source_or_test_defect_claim":False,"linked_public_exit_lki_mutant_log":ref(PROOF/"R3-original-entry-exit-lki-mutant/1.log"),"linked_public_incarnation_mutant_log":ref(PROOF/"R3-original-entry-incarnation-mutant/1.log")},
 "implementation_ready_for_acceptance":False,"acceptance":False,"current_independent_review":"in progress by /root/hushbringer_full_review_final",
 "pending_followup":["Independent full reviewer audits the corrected authoritative inputs against the same frozen source.","Root retains final clean committed-worker compilation, frozen-checker acceptance and Git ownership."],
 "source_ownership":"Not acquired for this metadata-only task; remains with root. No source writes occurred.",
 "commits":False,"pushes":False,"old_sealed_artifacts_modified":False
}
save("handoff.json",handoff)
(NEW/"handoff.md").write_text(
 "The complete maintainer matrix corrects four factual prose fields in R3-original-entry-exit-lki and R3-original-entry-incarnation. The public fixture establishes a functioning static +2/+2 grant before Hand-to-Battlefield entry, holds the original entry trigger unresolved, responds with Battlefield-to-Graveyard ChangeZone, then exiles the grant. The reentry sibling subsequently returns the same ObjectId from Graveyard to Battlefield as a new 1/1 incarnation. The original exit LKI is 3/3 against a 2/2 observer; the payoff is life 21 and the separate no-buff sibling remains 20.\n\n"
 "Both historical designated public mutant logs reach line 5152 and fail at 20 versus 21. Their exact source archives, manifests, commands, receipts, log hashes and unchanged helper bytes were rechecked. All 67 historical evidence payloads retain their original source/build identities. The other 65 rows are entirely unchanged; only package metadata changes outside the four corrected prose fields.\n\n"
 "Use "+str(NEW/"reviewed-map-selection.json")+" for the authoritative complete input set. Only the maintainer matrix JSON/Markdown is replaced. The remaining eight selected citation-fix artifacts remain byte-identical at their original paths. The complete JSON semantic delta and textual JSON/Markdown patch are retained in exact-delta.json and exact-delta.patch.\n\n"
 "All 2051 current source files and all 2051 frozen archive members match unchanged source "+EXPECTED+". All 32 prior citation-fix artifact files were rehashed unchanged. This task performed no source/test edits, compilation, runtime tests, card generation, mutation experiments, commits or pushes. Prior verification and all diagnostic, compatibility, parser and workspace limitations remain explicitly bound in handoff.json.\n\n"
 "The ongoing independent full reviewer owns the review verdict; root owns source, Git and final committed-worker acceptance. This artifact correction grants no acceptance and makes no new runtime or compilation claim.\n")
assert len(old_files) == 32
manifest = {str(p.relative_to(NEW)):digest(p) for p in sorted(NEW.rglob("*")) if p.is_file() and p.name not in ["manifest.json","receipt.json"]}
save("manifest.json",manifest)
receipt = {
 "sealed_utc":datetime.now(timezone.utc).isoformat(),"status":"sealed metadata-only correction; independent full review pending",
 "source_manifest_sha256":EXPECTED,"source_archive":ref(archive),"artifact_manifest":ref(NEW/"manifest.json"),
 "artifact_count":len(manifest),"handoff":ref(NEW/"handoff.json"),"handoff_markdown":ref(NEW/"handoff.md"),
 "corrected_map":ref(NEW/"production-path-maintainer-map.json"),"corrected_markdown":ref(NEW/"production-path-maintainer-map.md"),
 "authoritative_selection":ref(NEW/"reviewed-map-selection.json"),"exact_delta":ref(NEW/"exact-delta.json"),
 "source_unchanged":True,"historical_evidence_unchanged":True,"new_compilation":False,"new_runtime_tests":False,"acceptance":False,
 "source_ownership":"root; not acquired by artifact author","manifest_scope":"All package files except manifest.json and receipt.json. Receipt binds manifest; its hash is reported separately.",
 "permissions":"New package files 0444, directories 0555. No permissions or bytes changed on old artifacts or source."
}
save("receipt.json",receipt)
for p in NEW.rglob("*"):
    if p.is_file(): p.chmod(0o444)
for p in sorted([p for p in NEW.rglob("*") if p.is_dir()],reverse=True): p.chmod(0o555)
NEW.chmod(0o555)
assert all(digest(NEW/n)==h for n,h in manifest.items())
print(dump({"directory":str(NEW),"source":EXPECTED,"artifact_count":len(manifest),"source_files_verified":len(source_manifest),"old_package_files_unchanged":len(old_files),"historical_phase_archives_checked":6,"historical_runtime_logs_checked":18,"historical_payloads_unchanged":67,"handoff":ref(NEW/"handoff.json"),"map":ref(NEW/"production-path-maintainer-map.json"),"selector":ref(NEW/"reviewed-map-selection.json"),"manifest":ref(NEW/"manifest.json"),"receipt":ref(NEW/"receipt.json")}))
