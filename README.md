# AutoReview FinOps Bot 💰

An automated CI/CD watcher that blocks PRs introducing compute cost regressions into Python data pipelines. It intercepts unoptimized code, benchmarks it dynamically via a sandboxed Docker container, and calculates real Serverless execution costs over scale scenarios.

## 🚀 Quick Start (Copy-Paste Install)

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

ignore:
  - legacy/*
```
