"""Exact, rule-based jyotish tables for the 108 series (no AI): drishti houses and lagna dignity flips.
Run: python3 astro_tables.py > astro_tables.json"""
import json
RASHI = ["Mesh","Vrishabh","Mithun","Kark","Singh","Kanya","Tula","Vrishchik","Dhanu","Makar","Kumbh","Meen"]
GRAH = {
 "Surya":  {"own":["Singh"],"exalt":"Mesh","debil":"Tula","aspects":[7]},
 "Chandra":{"own":["Kark"],"exalt":"Vrishabh","debil":"Vrishchik","aspects":[7]},
 "Mangal": {"own":["Mesh","Vrishchik"],"exalt":"Makar","debil":"Kark","aspects":[4,7,8]},
 "Budh":   {"own":["Mithun","Kanya"],"exalt":"Kanya","debil":"Meen","aspects":[7]},
 "Guru":   {"own":["Dhanu","Meen"],"exalt":"Kark","debil":"Makar","aspects":[5,7,9]},
 "Shukra": {"own":["Vrishabh","Tula"],"exalt":"Meen","debil":"Kanya","aspects":[7]},
 "Shani":  {"own":["Makar","Kumbh"],"exalt":"Tula","debil":"Mesh","aspects":[3,7,10]},
 # Rahu/Ketu: 5/7/9 aspects and exaltation signs differ between schools -> always B items (hedged)
 "Rahu":   {"own":[],"exalt":None,"debil":None,"aspects":[7],"aspects_school_dependent":[5,9]},
 "Ketu":   {"own":[],"exalt":None,"debil":None,"aspects":[7],"aspects_school_dependent":[5,9]},
}
def sign_in_house(lagna_idx, house): return RASHI[(lagna_idx + house - 1) % 12]
def aspected_houses(house, offs): return sorted(((house - 1 + o - 1) % 12) + 1 for o in offs)
out = {}
for g, d in GRAH.items():
    for h in range(1, 13):
        flips = {"own": [], "exalt": [], "debil": []}
        for li, L in enumerate(RASHI):
            s = sign_in_house(li, h)
            if s in d["own"]: flips["own"].append(L)
            if s == d["exalt"]: flips["exalt"].append(L)
            if s == d["debil"]: flips["debil"].append(L)
        e = {"grah": g, "ghar": h, "drishti_on_houses": aspected_houses(h, d["aspects"]),
             "lagna_where_own_sign": flips["own"], "lagna_where_exalted": flips["exalt"], "lagna_where_debilitated": flips["debil"]}
        if d.get("aspects_school_dependent"): e["drishti_school_dependent"] = aspected_houses(h, d["aspects_school_dependent"])
        out[f"{g}-{h}"] = e
print(json.dumps(out, ensure_ascii=False, indent=1))
