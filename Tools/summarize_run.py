import io, json, os, sys

d = sys.argv[1]
rows = []
for ln in io.open(os.path.join(d, "status.jsonl"), encoding="utf-8"):
    ln = ln.strip()
    if ln.startswith("{"):
        rows.append(json.loads(ln))
    else:
        print("note:", ln)
if not rows:
    raise SystemExit("no status rows")
print("== state changes ==")
last = None
for r in rows:
    if r["state"] != last:
        print("t=%5.1f %-10s lv %d count %3d coins %5d kills %3d boss %s" % (r["t"], r["state"], r["level"], r["count"], r.get("coins", 0), r["kills"], r["boss"]))
        last = r["state"]
print("max count", max(r["count"] for r in rows), "| max coins", max(r.get("coins", 0) for r in rows), "| max parked", max(r.get("parked", 0) for r in rows), "| min fps", min(r["fps"] for r in rows), "| last t", rows[-1]["t"])
print("== every 5 s ==")
for r in rows[::10]:
    print("t=%5.1f %-9s lv%d c=%3d $=%5d k=%3d enemies=%2d parked=%2d wave=%d front=%-10s w=%-7s boss=%s x=%.1f alt=%.1f" % (
        r["t"], r["state"], r["level"], r["count"], r.get("coins", 0), r["kills"], r.get("enemies", 0), r.get("parked", 0), r.get("wave", 0), r.get("front", ""), r["weapon"], r["boss"], r["x"], r["alt"]))
log = os.path.join(d, "player.log")
if os.path.exists(log):
    txt = io.open(log, encoding="utf-8", errors="replace").read()
    n = txt.count("Exception")
    print("== exceptions in player.log:", n)
    if n:
        lines = txt.split("\n")
        for i, l in enumerate(lines):
            if "Exception" in l and "Licens" not in l:
                print("\n".join(lines[i:i + 3]))
                break
