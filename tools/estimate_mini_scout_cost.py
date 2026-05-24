#!/usr/bin/env python3
"""
Cost estimate for Mini Arena Scout strategy:
cheap prefilter -> send only top 1-3 interesting cards to GPT-5.5.
Prices from OpenAI API pricing page:
GPT-5.5: input $5/M, cached input $0.50/M, output $30/M.
GPT-5.4 mini: input $0.75/M, cached $0.075/M, output $4.50/M.
"""

MODELS = {
    "gpt-5.5": {"input": 5.00, "cached": 0.50, "output": 30.00},
    "gpt-5.4-mini": {"input": 0.75, "cached": 0.075, "output": 4.50},
}

SCENARIOS = {
    "top1_card": {"input_tokens": 1200, "cached_input_tokens": 0, "output_tokens": 350},
    "top3_cards": {"input_tokens": 2600, "cached_input_tokens": 0, "output_tokens": 650},
    "full_20_cards_bad": {"input_tokens": 12000, "cached_input_tokens": 0, "output_tokens": 1000},
}

RUNS_PER_DAY = [5, 10, 20, 50]

def cost(model, inp, cached, out):
    p = MODELS[model]
    return (inp / 1_000_000) * p["input"] + (cached / 1_000_000) * p["cached"] + (out / 1_000_000) * p["output"]

print("Mini Arena Scout cost estimate")
print("Strategy: prefilter locally, send only top 1-3 cards to GPT-5.5")
print()

for model in ["gpt-5.5", "gpt-5.4-mini"]:
    print("MODEL:", model)
    for name, s in SCENARIOS.items():
        one = cost(model, s["input_tokens"], s["cached_input_tokens"], s["output_tokens"])
        print(f"  {name}: ${one:.5f} per run | input={s['input_tokens']} output={s['output_tokens']}")
        for r in RUNS_PER_DAY:
            print(f"    {r:>2} runs/day: ${one*r:.4f}/day | ${one*r*30:.2f}/30d")
    print()

print("Recommended hard caps:")
print("- normal mode: max 3 cards per model call")
print("- max output: ~700 tokens")
print("- daily runs: start with 5-10")
print("- no model call if prefilter finds no clear card")
