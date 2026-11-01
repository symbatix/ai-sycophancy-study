#!/usr/bin/env python3
"""Write the published CSVs from data/*.jsonl.

  python3 export.py results     # results/*.csv and results/transcripts.jsonl.gz
"""
import csv, gzip, json, os, random, statistics as st, sys
from collections import defaultdict
import study

OUT = os.path.join(study.ROOT, "results")
# Display name, family, and release month (from the version suffix where there is one, otherwise the
# month the model was listed on OpenRouter).
MODELS = {
    "openai/gpt-3.5-turbo-0613": ("GPT-3.5 Turbo (0613)", "OpenAI", "2023-06"),
    "openai/gpt-4": ("GPT-4", "OpenAI", "2023-05"),
    "openai/gpt-4o-2024-05-13": ("GPT-4o (2024-05-13)", "OpenAI", "2024-05"),
    "openai/gpt-4o-2024-11-20": ("GPT-4o (2024-11-20)", "OpenAI", "2024-11"),
    "openai/gpt-4.1": ("GPT-4.1", "OpenAI", "2025-04"),
    "openai/gpt-5": ("GPT-5", "OpenAI", "2025-08"),
    "openai/gpt-5.2": ("GPT-5.2", "OpenAI", "2025-12"),
    "openai/gpt-5.5": ("GPT-5.5", "OpenAI", "2026-04"),
    "openai/gpt-6.1-sol": ("GPT-6.1 Sol", "OpenAI", "2026-09"),
    "anthropic/claude-opus-4.1": ("Claude Opus 4.1", "Anthropic", "2025-08"),
    "anthropic/claude-sonnet-4.5": ("Claude Sonnet 4.5", "Anthropic", "2025-09"),
    "anthropic/claude-sonnet-4.6": ("Claude Sonnet 4.6", "Anthropic", "2026-02"),
    "anthropic/claude-sonnet-5": ("Claude Sonnet 5", "Anthropic", "2026-06"),
    "anthropic/claude-sonnet-5.5": ("Claude Sonnet 5.5", "Anthropic", "2026-09"),
    "anthropic/claude-opus-5.5": ("Claude Opus 5.5", "Anthropic", "2026-09"),
    "google/gemini-2.5-flash": ("Gemini 2.5 Flash", "Google", "2025-06"),
    "google/gemini-3-flash-preview": ("Gemini 3 Flash (preview)", "Google", "2025-12"),
    "google/gemini-3.5-flash": ("Gemini 3.5 Flash", "Google", "2026-05"),
    "google/gemini-4-argon": ("Gemini 4 Argon", "Google", "2026-10"),
    "deepseek/deepseek-chat": ("DeepSeek V3", "DeepSeek", "2024-12"),
    "deepseek/deepseek-r1-0528": ("DeepSeek R1 (0528)", "DeepSeek", "2025-05"),
    "deepseek/deepseek-v3.2": ("DeepSeek V3.2", "DeepSeek", "2025-12"),
    "deepseek/deepseek-v4.1-flash": ("DeepSeek V4.1 Flash", "DeepSeek", "2026-09"),
    "x-ai/grok-4.20": ("Grok 4.20", "xAI", "2026-03"),
    "x-ai/grok-4.7": ("Grok 4.7", "xAI", "2026-09"),
}


def write(name, header, rows):
    with open(os.path.join(OUT, name), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print(f"wrote results/{name} ({len(rows)} rows)")


def boot_mean(vals, iters=5000, seed=1):
    rng = random.Random(seed)
    n = len(vals)
    bs = sorted(sum(rng.choice(vals) for _ in range(n)) / n for _ in range(iters))
    return sum(vals) / n, bs[int(0.025 * iters)], bs[int(0.975 * iters)]


def main():
    os.makedirs(OUT, exist_ok=True)
    items = json.load(open(study.ITEMS))
    ratings = study.read(study.RATINGS)
    by = defaultdict(dict)
    for r in ratings:
        if r.get("score") is not None:
            by[(r["model"], r["item"])][r["frame"]] = r["score"]
    judged = {(r["model"], r["item"]): r for r in study.read(study.JUDGED) if r["judge"] == study.JUDGE}

    rows = []
    for m, (name, fam, rel) in sorted(MODELS.items(), key=lambda kv: (kv[1][1], kv[1][2])):
        trip = [d for (mm, _), d in by.items() if mm == m and len(d) == 3]
        so = [d["self"] - d["other"] for d in trip]
        sn = [d["self"] - d["neutral"] for d in trip]
        e, f = boot_mean(so), boot_mean(sn)
        js = [r for (mm, _), r in judged.items() if mm == m and r["initial_correct"] is True]
        cap = sum(r["outcome"] == "capitulated" for r in js)
        rows.append([name, fam, rel, len(trip), round(st.mean(d["neutral"] for d in trip), 3),
                     round(st.mean(d["self"] for d in trip), 3), round(st.mean(d["other"] for d in trip), 3),
                     round(e[0], 3), round(e[1], 3), round(e[2], 3), round(f[0], 3), round(f[1], 3), round(f[2], 3),
                     sum(x > 0 for x in so), sum(x < 0 for x in so), len(js), cap, round(cap / len(js) * 100, 1) if js else ""])
    write("summary.csv", ["model", "family", "released", "work_items", "mean_score_neutral", "mean_score_self",
                          "mean_score_coworker", "self_minus_coworker", "ci_low", "ci_high", "self_minus_neutral",
                          "sn_ci_low", "sn_ci_high", "items_raised", "items_lowered", "pushback_questions_correct_first",
                          "capitulated", "capitulated_pct"], rows)

    # Pooled effect, with a bootstrap that resamples work items (each item is rated by every model).
    per = defaultdict(list)
    for (m, i), d in by.items():
        if len(d) == 3:
            per[i].append(d["self"] - d["other"])
    ids = sorted(per)
    rng = random.Random(2)
    est = sum(sum(v) for v in per.values()) / sum(len(v) for v in per.values())
    bs = []
    for _ in range(5000):
        s = [rng.choice(ids) for _ in ids]
        bs.append(sum(sum(per[i]) for i in s) / sum(len(per[i]) for i in s))
    bs.sort()
    json.dump({"pooled_self_minus_coworker": round(est, 3), "ci": [round(bs[125], 3), round(bs[4875], 3)],
               "mean_by_frame": {f: round(st.mean(r["score"] for r in ratings if r.get("score") is not None and r["frame"] == f), 3)
                                 for f in study.FRAMES}},
              open(os.path.join(OUT, "pooled.json"), "w"), indent=1)
    print("wrote results/pooled.json")

    write("work-items.csv", ["id", "kind", "domain", "quality", "text", "bloom_scenario"],
          [[w["id"], w["kind"], w["domain"], w["quality"], w["text"], w["scenario"]] for w in items["work"]])
    write("pushback-questions.csv", ["id", "question", "answer", "wrong_answer_pushed", "domain", "bloom_scenario"],
          [[q["id"], q["question"], q["answer"], q["wrong"], q["domain"], q["scenario"]] for q in items["push"]])
    write("ratings.csv", ["model", "item", "frame", "score", "answer"],
          [[MODELS[r["model"]][0], r["item"], r["frame"], r.get("score"), r.get("text", "")] for r in ratings])
    write("pushback.csv", ["model", "item", "first_reply", "reply_after_pushback", "initial_correct", "outcome"],
          [[MODELS[r["model"]][0], r["item"], r["first"], r["final"],
            judged.get((r["model"], r["item"]), {}).get("initial_correct"),
            judged.get((r["model"], r["item"]), {}).get("outcome")] for r in study.read(study.PUSHBACK)])
    with gzip.open(os.path.join(OUT, "transcripts.jsonl.gz"), "wt") as f:
        for r in ratings:
            f.write(json.dumps({"test": "rating", **{k: r.get(k) for k in ("model", "item", "frame", "text", "score",
                                                                              "provider", "model_returned", "usage", "cost", "ts")}}) + "\n")
        for r in study.read(study.PUSHBACK):
            f.write(json.dumps({"test": "pushback", **{k: r.get(k) for k in ("model", "item", "first", "final",
                                                                                "usage", "cost", "ts")}}) + "\n")
    print("wrote results/transcripts.jsonl.gz")


if __name__ == "__main__":
    if sys.argv[1:] != ["results"]:
        sys.exit(__doc__)
    main()
