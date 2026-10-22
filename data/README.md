# Data Directory

## sample_urls.csv

**This is test/illustrative data only. Do NOT use it for real phishing detection evaluation.**

A small dataset of 20 URLs (10 legitimate, 10 phishing-like) provided for software testing and smoke tests.

**Format:**
- `url`: The URL string
- `label`: 0 = legitimate, 1 = phishing

## Using Your Own Dataset

To train Q-Sentinel with a real dataset, you need a CSV file with:

1. **A URL column** (default name: `url`)
2. **A label column** (default name: `label`)
3. **At least 100+ URLs** (more is better, ideally 1000+)

### Example Format

```csv
url,label
https://www.legitimate-bank.com,legitimate
https://www.phishing-copy.tk,phishing
https://github.com/user/repo,legitimate
http://confirm-password@fake-bank.ru,phishing
```

### Recommended Public Datasets

1. **Phishing URL Dataset (Kaggle)**
   - Search: "Phishing URL" on Kaggle
   - CSV typically has columns like `URL`, `Label` or similar
   - Map columns using `--url-column` and `--label-column` flags

2. **UCI Machine Learning Repository**
   - Phishing Websites Dataset
   - http://archive.ics.uci.edu/ml/

### How to Train with Your Dataset

```bash
# If your dataset uses different column names and label values:
python train.py \
  --data your_dataset.csv \
  --url-column "website_url" \
  --label-column "status" \
  --label-mapping '{"phishing": 1, "legitimate": 0}'
```

### Label Mapping

If your dataset uses different labels:

```bash
# Binary string labels
python train.py --data data.csv --label-mapping '{"phishing": 1, "safe": 0}'

# Integer labels (if not already 0/1)
python train.py --data data.csv --label-mapping '{"-1": 1, "1": 0}'
```

## Important Notes

- **DO NOT commit real labelled datasets** to version control (too large, may contain sensitive URLs)
- **Ensure data quality**: Remove duplicates, check for missing values, validate URLs
- **Balance matters**: Try to have roughly equal phishing and legitimate URLs
- **Test set**: By default, 20% of data is held out for evaluation
- **No personal data**: Phishing detection should not require user PII

## Dataset Quality Checklist

Before training:
- [ ] CSV is readable and columns exist
- [ ] No missing/null values in URL or label columns
- [ ] URLs are strings (not corrupted)
- [ ] Labels are consistent (all 0/1, all phishing/legitimate, etc.)
- [ ] Dataset has both classes (both phishing and legitimate)
- [ ] Minimum 20+ URLs (realistically 100+)
