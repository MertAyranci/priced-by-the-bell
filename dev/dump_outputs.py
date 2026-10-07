import json,sys
nb=json.load(open(sys.argv[1]))
for i,c in enumerate(nb["cells"]):
    if c["cell_type"]!="code": continue
    for o in c.get("outputs",[]):
        d=o.get("data",{})
        txt=o.get("text") or d.get("text/plain") or o.get("evalue")
        if txt: print(f"--- cell {i}"); print("".join(txt)[:3500])
