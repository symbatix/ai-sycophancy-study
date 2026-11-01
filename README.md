# Does AI rate your work higher if you say you wrote it?

Code and data for the [Heldout Labs](https://heldoutlabs.com) study **[Does AI rate your work higher if you say you wrote it? We tested 25 versions of ChatGPT, Claude, Gemini, DeepSeek and Grok](https://heldoutlabs.com/ai-rates-your-work-higher)** (November 2026).

25 model versions (OpenAI, Anthropic, Google, DeepSeek, xAI; 2023 to 2026) rated the same 40 pieces of work on a 1-10 scale three times each: framed as "I wrote this", "my coworker wrote this" and neutral. They also answered 40 factual questions and were then told the answer was wrong.

## Results

- **"I wrote this" adds 0.25 points** out of 10 over "my coworker wrote this" (95% CI 0.20 to 0.30), pooled over 3,000 ratings; 15 of 25 models individually exclude zero. Largest: GPT-4.1 (+0.47), GPT-5.2 (+0.46), Gemini 3 Flash (+0.41), GPT-5.5 (+0.40).
- **Newer models grade flawed work about 2 points lower**: e.g. GPT-4o (May 2024) 7.4 vs GPT-6.1 Sol 5.0; DeepSeek V3 7.2 vs V4.1 Flash 4.7.
- **Pushback rarely flips a correct answer**: 12 of 994 conversations (1.2%).

Per-model results are in [`results/summary.csv`](results/summary.csv) and in the article.

## Repository

| Path | Contents |
|---|---|
| `bloomcfg/behaviors.json` | The two behavior descriptions given to Bloom |
| `bloom_ideate.py` | Runs Bloom's understanding and ideation stages to generate test scenarios |
| `results/transcripts/<behavior>/` | Bloom's output: `understanding.json`, `ideation.json` (40 scenarios each) |
| `study.py` | Turns scenarios into test items, verifies questions, runs the models, classifies pushback outcomes, reports |
| `export.py` | Writes the published CSVs, with bootstrap confidence intervals |
| `data/items.json` | The 40 pieces of work and 40 pushback questions |
| `data/ratings.jsonl` | All 3,000 rating answers, with token usage and cost |
| `data/pushback.jsonl` | All 1,000 pushback conversations |
| `data/pushback_judged.jsonl` | Outcome classifications (DeepSeek v4.1 Flash for all; Claude Haiku 5.5 for a random 300) |
| `results/*.csv` | The published summary, items, ratings and pushback tables |

## Reproduce

The analysis needs only Python 3 (standard library) and the data in this repo:

```sh
python3 study.py report           # bonus and pushback outcomes by model
python3 export.py results         # results/*.csv
```

Re-running needs an [OpenRouter](https://openrouter.ai) key in `.env` (see `.env.example`). Generating new scenarios also needs a checkout of [Bloom](https://github.com/safety-research/bloom) (set `BLOOM_SRC` to its `src` folder). Model responses are not deterministic, so new runs will differ in detail.

```sh
BLOOM_SRC=../bloom/src python3 bloom_ideate.py ownership-sycophancy 40
BLOOM_SRC=../bloom/src python3 bloom_ideate.py pushback-capitulation 40
python3 study.py items --budget 3
python3 study.py verify --budget 2
python3 study.py run --models openai/gpt-6.1-sol,anthropic/claude-sonnet-5.5 --budget 5
python3 study.py judge --budget 1
python3 study.py report
```

`--budget` is a hard spending cap in USD, enforced from OpenRouter's per-request cost.

Full methodology and limitations: [heldoutlabs.com/ai-rates-your-work-higher](https://heldoutlabs.com/ai-rates-your-work-higher).

## License

Code: [MIT](LICENSE). Data (`data/`, `results/`): [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Please cite:

> symbatix (2026). "Does AI rate your work higher if you say you wrote it? We tested 25 versions of ChatGPT, Claude, Gemini, DeepSeek and Grok." Heldout Labs. https://heldoutlabs.com/ai-rates-your-work-higher
