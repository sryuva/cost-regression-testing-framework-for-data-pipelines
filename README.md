# AutoReview FinOps Bot 💰

An automated CI/CD watcher that blocks PRs introducing compute cost regressions into Python data pipelines. It intercepts unoptimized code, benchmarks it dynamically via a sandboxed Docker container, and calculates real Serverless execution costs over scale scenarios (e.g., 10k runs/day). 

If a cheaper equivalent exists natively, it blocks the PR and injects a `git apply` patch for engineers to grab immediately.

## 🚀 Quick Start
Integrate directly into any GitHub workflow natively catching PR modifications:

```yaml
steps:
  - name: Run AutoReview FinOps Pipeline
    uses: yourusername/autoreview@v1
    with:
      pr_file: path/to/pr_pipeline.py
      main_file: path/to/main_pipeline.py
      openai_api_key: ${{ secrets.OPENAI_API_KEY }}
```

## Example Output
When code fails the FinOps thresholds against the `main` branch, the bot outputs explicitly:

```text
❌ Cost Regression Detected
+28% increase (~+$1,200/month at scale).

Top issue:
- df.apply() causing massive runtime execution slowdowns.

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
