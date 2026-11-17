import json
import subprocess
import sys
trace = "10 0 0\n10 1 119\n10 2 120\n10 3 299\n10 4 300\n"
p = subprocess.run([sys.argv[1]], input=trace, text=True, capture_output=True, timeout=10, check=True)
rows = [json.loads(x) for x in p.stdout.splitlines()]
events = [x for x in rows if x.get("event") == "LOCAL_TEST_TRIGGER"]
assert [x["id"] for x in events] == [1, 2], rows
assert all(x["submitted"] is False for x in rows), rows
print(json.dumps(dict(status="PASS", scope="real compiled rcheevos local conditions", triggers=len(events))))
