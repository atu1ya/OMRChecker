# Everest Tutoring ASET Marking System

## Overview
This app wraps the existing OMR engine with a staff-only web interface. It accepts PNG scans, compares them to uploaded answer keys, and returns annotated PDFs plus a branded report.

## Quick start

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Create a `.env` file:

```bash
python scripts/setup_env.py
```

3. Run the dev server:

```bash
python scripts/run_dev.py
```

4. Visit `http://localhost:8000` and log in with the staff password.

## Configuration upload

Upload three files on the dashboard:

- **Reading answer key** (`.csv`, `.txt`, or `.json`)
- **QR/AR answer key** (`.csv`, `.txt`, or `.json`)
- **Concept mapping** (`.json`)

### Answer key formats

**CSV/TXT** (one row per question):

```text
RC1,A
RC2,B
```

**JSON**:

```json
{
  "RC1": "A",
  "RC2": "B"
}
```

### Concept mapping format

```json
{
  "Reading": {
    "Vocabulary": ["RC1", "RC2"],
    "Comprehension": ["RC3", "RC4"]
  },
  "QR": {
    "Number": ["QR1", "QR2"]
  },
  "AR": {
    "Algebra": ["AR1", "AR2"]
  }
}
```

## Single student workflow

- Upload reading + QR/AR PNGs.
- Enter student name and writing score.
- Download a ZIP containing:
  - `<student>_reading_marked.pdf`
  - `<student>_qrar_marked.pdf`
  - `<student>_report.pdf`
  - `<student>_results.json`

## Batch workflow

Manifest example:

```json
{
  "students": [
    {
      "name": "Ada Lovelace",
      "writing_score": 25,
      "reading_sheet": "ada_reading.png",
      "qrar_sheet": "ada_qrar.png"
    }
  ]
}
```

ZIP the referenced PNGs. The output ZIP contains a folder per student plus a `summary.json`.

## Templates

Templates live in `config/`. The reference alignment images must be provided alongside:

- `config/reference_reading.jpg`
- `config/reference.png`

## Deployment notes

- Set `STAFF_PASSWORD` and `SECRET_KEY` in the environment.
- The service is stateless and stores session configuration in memory only.
