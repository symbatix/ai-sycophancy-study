"""Generate test scenarios with Anthropic's Bloom (understanding + ideation stages only).

  BLOOM_SRC=/path/to/bloom/src python3 bloom_ideate.py <behavior> <n>

Needs a checkout of Bloom (https://github.com/safety-research/bloom) and its dependencies.
Writes results/transcripts/<behavior>/{understanding,ideation}.json under this folder.
"""
import os, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
for line in open(HERE / ".env"):
    if line.startswith("OPENROUTER_API_KEY="):
        os.environ["OPENROUTER_API_KEY"] = line.split("=", 1)[1].strip()
sys.path.insert(0, os.environ.get("BLOOM_SRC", str(HERE.parent / "bloom" / "src")))
os.chdir(HERE)

from bloom.stages.step1_understanding import run_understanding
from bloom.stages.step2_ideation import run_ideation

behavior, n = sys.argv[1], int(sys.argv[2])
model = "openrouter/anthropic/claude-sonnet-5.5"
config = {
    "behavior": {"name": behavior, "examples": []},
    "temperature": 1.0, "evaluator_reasoning_effort": "none", "target_reasoning_effort": "none",
    "max_concurrent": 8, "configurable_prompts": "default", "anonymous_target": True, "debug": False,
    "understanding": {"model": model, "max_tokens": 8000},
    "ideation": {"model": model, "total_evals": n, "diversity": 1.0, "max_tokens": 64000, "web_search": False},
    "rollout": {"modality": "conversation", "max_turns": 2, "no_user_mode": False},
    "_config_dir": HERE / "bloomcfg",
}
run_understanding(config=config)
run_ideation(config=config)
print("done", behavior)
