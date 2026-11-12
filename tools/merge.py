"""Merge new or updated listings into jobs.json and drop closed ones.

Usage: python3 tools/merge.py new.json [--remove ids.txt]
new.json: a JSON list of listings in the KaziRadar format (same fields as jobs.json).
Listings with an existing id (or the same title+company+location) replace the old copy.
"""
import json, hashlib, sys, datetime, pathlib

root = pathlib.Path(__file__).resolve().parent.parent
path = root / "jobs.json"
data = json.loads(path.read_text()) if path.exists() else {"jobs": []}
jobs = {j["id"]: j for j in data.get("jobs", [])}
key = lambda j: (j["title"].strip().lower(), j["company"].strip().lower(), j.get("location", "").strip().lower())

def ident(j):
    return hashlib.sha1(f'{j["url"]}|{j["title"]}|{j.get("location","")}'.encode()).hexdigest()[:16]

added = updated = 0
if len(sys.argv) > 1 and sys.argv[1] != "--remove":
    for j in json.loads(pathlib.Path(sys.argv[1]).read_text()):
        j.setdefault("id", ident(j))
        j.setdefault("official", True)
        same = [i for i, o in jobs.items() if key(o) == key(j)]
        if j["id"] in jobs or same:
            for i in same: jobs.pop(i, None)
            updated += 1
        else:
            added += 1
        jobs[j["id"]] = j

removed = 0
if "--remove" in sys.argv:
    for i in pathlib.Path(sys.argv[sys.argv.index("--remove") + 1]).read_text().split():
        removed += jobs.pop(i, None) is not None

now = datetime.datetime.now(datetime.timezone.utc)
open_jobs = [j for j in jobs.values() if datetime.datetime.fromisoformat(j["deadline"]) > now]
closed = len(jobs) - len(open_jobs)
out = {"last_collected": now.replace(microsecond=0).isoformat(), "count": len(open_jobs),
       "jobs": sorted(open_jobs, key=lambda j: j["deadline"])}
path.write_text(json.dumps(out, ensure_ascii=False, indent=0))
print(f"added {added}, updated {updated}, removed {removed}, dropped closed {closed}, open now {len(open_jobs)}")
