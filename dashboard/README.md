# Dashboard

This folder contains a lightweight React-based dashboard used to visualize benchmark results.

The static files are uploaded to an Amazon S3 bucket via the `dashboard_sync.yml` workflow.
Benchmark metrics (`completed_commits.json` and the `results/` directory) are stored in the same bucket so the dashboard can fetch them directly.

## Custom base path

If the metrics are stored under a prefix other than the bucket root, pass a `base` query parameter when loading `index.html`:

```
https://<bucket-url>/dashboard/index.html?base=path/to/prefix
```

The dashboard will prepend this prefix when requesting `completed_commits.json` and per-commit metrics files.
