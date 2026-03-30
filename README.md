# AutoReview

Catch expensive code before it hits production.

Every PR shows its cost impact — and flags regressions before they merge.

“Like tests catch bugs, AutoReview catches expensive code.”

An automated CI/CD watcher that blocks PRs introducing compute cost regressions into Python data pipelines. It benchmarks code dynamically via a sandboxed Docker container and calculates real Serverless execution costs.

> [!TIP]
> **No-AI Mode**: Works fully without AI. Uses deterministic benchmarking to compare PRs against the main branch. AI optimization suggestions are only triggered if an API key is provided.

## 🚀 Quick Start (Copy-Paste Install)

Works out of the box with no API keys.
AI suggestions are optional.

Drop this into `.github/workflows/autoreview.yml`:

```yaml
name: AutoReview Cost Checker
on: [pull_request]

jobs:
  finops_check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Get baseline
        run: |
          git fetch origin main
          git show origin/main:path/to/pipeline.py > baseline.py

      - name: Run AutoReview
        uses: your_username/autoreview@v1
        with:
          pr_file: path/to/pipeline.py
          main_file: baseline.py
          openai_api_key: ${{ secrets.OPENAI_API_KEY }}
```

## Example Output

❌ **Cost Regression Detected**
+28% compute increase
~+$1,200/month

**Top issue**:
- `df.apply()` causing massive runtime execution slowdowns.

> [!NOTE]
> Projections are estimates based on sampled execution and assumed workload frequency. 
> Accurate results depend heavily on the quality and representativeness of provided test inputs.

```text
💰 Cost Impact (Serverless-equivalent GB-seconds)
Estimated Monthly Savings if Optimized:
   1k runs/day:  $120
  10k runs/day:  $1,200  <-- default
  50k runs/day:  $6,000

[Apply Optimization Patch] (Copy/Paste below)
git apply <<EOF
--- a/path/to/pr_pipeline.py
+++ b/path/to/pr_pipeline.py
...
EOF
```

## Configuration
Add an `.autoreview.yml` to your project root to tune thresholds:
```yaml
min_impact: 10          # Require >10% savings to block PR
fail_on_regression: true
runs_per_day: 10000     # Adjust assumed monthly execution volume
track_history: true     # Record cost trends across PRs

ignore:
  - legacy/*
```
