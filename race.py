"""Single-dispatch fictitious GitHub ref-create race; no AI, no FILCKO data."""
import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from urllib.error import HTTPError
from urllib.request import Request, urlopen

PREFIX = "orchestration-fixture-004"
AUTH = "fixture-go-004-001"
PAYLOAD = {"issue": "FICTIVE-004", "tasks": ["Classer ALPHA avant BETA"]}
API = "https://api.github.com"
REPO = os.environ.get("GITHUB_REPOSITORY", "")
SHA = os.environ.get("GITHUB_SHA", "")
RUN = os.environ.get("GITHUB_RUN_ID", "")
BASE = "/repos/" + REPO

def require(condition, reason):
    if not condition:
        raise RuntimeError(reason)

def encode(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))

def api(method, path, data=None, allowed=(200,)):
    req = Request(API + path, method=method,
        data=None if data is None else encode(data).encode(),
        headers={"Authorization": "Bearer " + os.environ["GH_TOKEN"],
                 "Accept": "application/vnd.github+json",
                 "X-GitHub-Api-Version": "2022-11-28",
                 "Content-Type": "application/json"})
    try:
        with urlopen(req, timeout=15) as response:
            status, body = response.status, response.read(250000)
    except HTTPError as exc:
        status, body = exc.code, exc.read(250000)
    require(status in allowed, "HTTP_" + str(status))
    return status, json.loads(body) if body else None

def ref(name):
    return api("GET", BASE + "/git/ref/tags/" + name, allowed=(200, 404))

def now():
    return datetime.now(timezone.utc).timestamp()

def context():
    require(REPO and SHA and RUN, "MISSING_CONTEXT")
    require(REPO == "CedricDeLaVega/orchestration-fixture-004", "WRONG_REPOSITORY")
    require(os.environ["GITHUB_RUN_ATTEMPT"] == "1", "RERUN_REFUSED")
    require(os.environ["GITHUB_EVENT_NAME"] == "workflow_dispatch", "MANUAL_ONLY")
    require(os.environ["GITHUB_REF"] == "refs/heads/main", "MAIN_ONLY")
    require(os.environ["GITHUB_WORKFLOW_REF"] ==
            REPO + "/.github/workflows/race.yml@refs/heads/main", "WRONG_WORKFLOW")
    _, repo = api("GET", BASE)
    require(repo["visibility"] == "public" and not repo["fork"], "WRONG_REPO")
    require(str(repo["owner"]["id"]) == os.environ["GITHUB_ACTOR_ID"], "OWNER_ONLY")
    _, main = api("GET", BASE + "/git/ref/heads/main")
    require(main["object"]["sha"] == SHA, "MAIN_CHANGED")
    return {"authorization": AUTH, "repository": REPO, "workflow_sha": SHA,
            "run_id": RUN,
            "payload_hash": hashlib.sha256(encode(PAYLOAD).encode()).hexdigest()}

def read_tag(name, capsule):
    status, reference = ref(name)
    if status == 404:
        return None
    require(reference["object"]["type"] == "tag", "NOT_ANNOTATED")
    _, tag = api("GET", BASE + "/git/tags/" + reference["object"]["sha"])
    record = json.loads(tag["message"])
    require(record["capsule"] == capsule, "TAG_CONTEXT_MISMATCH")
    require(tag["object"]["type"] == "commit" and tag["object"]["sha"] == SHA, "TAG_TARGET_MISMATCH")
    return reference["object"]["sha"], record

def report(message):
    print(message, flush=True)
    with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as stream:
        stream.write(message + "\n")

def claim():
    capsule = context()
    candidate = os.environ["CANDIDATE"]
    require(candidate in ("A", "B"), "INVALID_CANDIDATE")
    other = "B" if candidate == "A" else "A"
    consumed = PREFIX + "/consumed/" + AUTH
    require(ref(consumed)[0] == 404, "ALREADY_CONSUMED")
    for label in ("A", "B"):
        existing = read_tag(PREFIX + "/ready/" + AUTH + "/" + label, capsule)
        require(not existing or label != candidate, "ALREADY_READY")
    record = {"capsule": capsule, "candidate": candidate, "ready_at": now()}
    _, tag = api("POST", BASE + "/git/tags", {
        "tag": AUTH + "-" + RUN + "-" + candidate,
        "message": encode(record), "object": SHA, "type": "commit",
        "tagger": {"name": "Fictitious race", "email": "fixture@example.invalid",
                   "date": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    }, allowed=(201,))
    own_sha = tag["sha"]
    api("POST", BASE + "/git/refs",
        {"ref": "refs/tags/" + PREFIX + "/ready/" + AUTH + "/" + candidate,
         "sha": own_sha}, allowed=(201,))
    peer = None
    deadline = time.monotonic() + 65
    while time.monotonic() < deadline:
        peer = read_tag(PREFIX + "/ready/" + AUTH + "/" + other, capsule)
        if peer:
            break
        time.sleep(1)
    require(peer is not None, "NO_PEER_INCONCLUSIVE")
    require(peer[1]["candidate"] == other, "INVALID_PEER")
    target = max(record["ready_at"], peer[1]["ready_at"]) + 15
    require(now() < target - 2, "BARRIER_MISSED_INCONCLUSIVE")
    while now() < target:
        time.sleep(min(0.05, max(0.001, target - now())))
    started = now()
    status, _ = api("POST", BASE + "/git/refs",
        {"ref": "refs/tags/" + consumed, "sha": own_sha}, allowed=(201, 409, 422))
    ended = now()
    winner = read_tag(consumed, capsule)
    require(winner is not None, "NO_WINNER_REFERENCE")
    if status == 201:
        require(winner[0] == own_sha, "WINNER_MISMATCH")
        outcome = "ACCEPTED"
    else:
        require(winner[0] == peer[0] and winner[1]["candidate"] == other,
                "REJECTION_WITHOUT_VERIFIED_WINNER")
        outcome = "REFUSED_CONSUMED"
    receipt = {"candidate": candidate, "capsule": capsule, "outcome": outcome,
               "status": status, "object_sha": own_sha, "winner_sha": winner[0],
               "target": target, "started": started, "ended": ended}
    if outcome == "ACCEPTED":
        receipt["result"] = "ALPHA, BETA"
    with open(os.environ["GITHUB_OUTPUT"], "a") as stream:
        stream.write("receipt=" + encode(receipt) + "\n")
    report(encode(receipt))

def verify():
    capsule = context()
    require(os.environ["STATUS_A"] == os.environ["STATUS_B"] == "success", "MISSING_CANDIDATE_INCONCLUSIVE")
    a, b = [json.loads(os.environ["RECEIPT_" + c]) for c in ("A", "B")]
    require(a["candidate"] == "A" and b["candidate"] == "B", "INVALID_RECEIPTS")
    require(a["capsule"] == b["capsule"] == capsule, "CAPSULE_MISMATCH")
    require(sorted([a["outcome"], b["outcome"]]) == ["ACCEPTED", "REFUSED_CONSUMED"], "NOT_EXACTLY_ONE_WINNER")
    winner = a if a["outcome"] == "ACCEPTED" else b
    loser = b if winner is a else a
    require(winner["status"] == 201, "INVALID_WINNER_HTTP")
    require(loser["status"] in (409, 422), "INVALID_LOSER_HTTP")
    require(winner["result"] == "ALPHA, BETA" and "result" not in loser, "INVALID_RESULT")
    require(a["target"] == b["target"], "DIFFERENT_BARRIERS")
    require(max(a["started"], b["started"]) < min(a["ended"], b["ended"]), "NO_OBSERVED_CALL_OVERLAP_INCONCLUSIVE")
    final = read_tag(PREFIX + "/consumed/" + AUTH, capsule)
    require(final and final[0] == winner["object_sha"] == loser["winner_sha"], "FINAL_REFERENCE_MISMATCH")
    for receipt in (a, b):
        ready = read_tag(PREFIX + "/ready/" + AUTH + "/" + receipt["candidate"], capsule)
        require(ready and ready[0] == receipt["object_sha"], "READY_MISMATCH")
    references = []
    for namespace in ("heads", "tags"):
        _, items = api("GET", BASE + "/git/matching-refs/" + namespace + "/")
        references.extend(items)
    expected = {"refs/heads/main", "refs/tags/" + PREFIX + "/ready/" + AUTH + "/A",
                "refs/tags/" + PREFIX + "/ready/" + AUTH + "/B",
                "refs/tags/" + PREFIX + "/consumed/" + AUTH}
    require({item["ref"] for item in references} == expected, "UNEXPECTED_REFS")
    report("PASS technique : un gagnant, un refus, un seul résultat; désactivation à suivre.")

if __name__ == "__main__":
    try:
        require(sys.argv[1:] in (["claim"], ["verify"]), "INVALID_MODE")
        (claim if sys.argv[1] == "claim" else verify)()
    except Exception as exc:
        message = str(exc) if type(exc) is RuntimeError else type(exc).__name__
        print("STOP: " + message, file=sys.stderr)
        sys.exit(1)
