"""data/walltime.json from the paper's own Fig. 5 pipeline (make_headline.py): mean ± SD over three seeds vs training minutes."""
import json, sys
sys.path.insert(0, sys.argv[1])
import make_headline as H
curves = H.curves_for(H.load_points()["Science Q&A"], "time")
res = H.comparison(curves)
key = {"offpolicy": "off", "ssd": "ssd", "onpolicy": "on"}
out = {"task": "Science Q&A", "series": {}, "arrow": {"on": res["onpolicy"], "ssd": res["ssd"]},
       "saving": round(res["saving_percent"]), "source": "paper files/plots/headline/make_headline.py (Fig. 5)"}
for m, k in key.items():
    x, mean, sd = curves[m]
    out["series"][k] = {"x": [round(float(v), 2) for v in x], "y": [round(float(v), 2) for v in mean], "sd": [round(float(v), 2) for v in sd]}
json.dump(out, open(sys.argv[2], "w"))
print(res, {k: len(v["x"]) for k, v in out["series"].items()})
