# AI Volunteer & Internship Matching Platform — Working Prototype

A content-based recommendation system that matches students/professionals with
internships, NGO projects, and volunteer opportunities.

## What's included

| File | Purpose |
|---|---|
| `generate_data.py` | Creates realistic synthetic datasets (200 users, 80 orgs) so you can test immediately |
| `recommender.py` | The core AI engine: cleaning, TF-IDF + cosine similarity, rule-based scoring, ranking |
| `database.py` | SQLite persistence layer (users, organizations, applications) |
| `app.py` | Streamlit web app: registration forms, recommendation page, analytics dashboard |
| `requirements.txt` | Dependencies |

## Setup

```bash
pip install -r requirements.txt

# 1. Generate sample data (optional if you already have real data)
python generate_data.py

# 2. Initialize the database and load sample data into it
python database.py

# 3. Launch the app
streamlit run app.py
```

## 🌐 Live Demo

https://skillbridgeai01.streamlit.app/

## Run Locally

Install the dependencies:

```bash
pip install -r requirements.txt
```

Run the app:

```bash
streamlit run app.py
```

If running locally, open the URL Streamlit prints (usually http://localhost:8501).

## How the matching engine works

For every (user, opportunity) pair, we compute a weighted compatibility score:

```
final_score = 0.50 * skill_interest_similarity   (TF-IDF + cosine similarity)
            + 0.20 * location_score               (remote=1.0, same city=1.0, hybrid=0.6, else 0.2)
            + 0.10 * availability_score            (flexible/full-time score higher)
            + 0.10 * education_score               (meets/exceeds eligibility)
            + 0.10 * experience_score              (meets/exceeds minimum experience)
```

`skill_interest_similarity` comes from vectorizing each user's
`skills + interests + preferred_domain` and each opportunity's
`required_skills + domain + role` with TF-IDF, then taking cosine similarity —
this is the "88% match" style score from the spec.

Weights live in `WEIGHTS` at the top of `recommender.py` — tune them once you
have real feedback data (Step 6: "improve the recommendation algorithm over time").

## Extending it (per the original roadmap)

- **Prediction model (selection likelihood):** once you have real `applications`
  data with outcomes (selected / not selected), train a `RandomForestClassifier`
  or `LogisticRegression` on `[match_score, skill_score, location_score, experience]`
  → `selected (0/1)`. Scikit-learn is already a dependency.
- **Resume parsing:** add a skill using `pdfplumber`/`python-docx` to extract text,
  then run it through a skill-keyword extractor (spaCy `PhraseMatcher` against
  `SKILLS_POOL`) before calling `standardize_skill_string`.
- **Notifications:** cron job or APScheduler that checks `organizations` for new
  rows since last run and emails users whose `preferred_domain`/`skills` match.
- **MySQL instead of SQLite:** swap `sqlite3.connect(...)` in `database.py` for
  `mysql.connector.connect(...)` or SQLAlchemy — the rest of the code (pandas
  `to_sql`/`read_sql`) works unchanged.
- **Power BI dashboard:** point Power BI at `data/users.csv` / `data/organizations.csv`
  or directly at the SQLite file via an ODBC connector, instead of (or alongside)
  the Plotly charts in the Streamlit dashboard.

## Notes

- `generate_data.py` gives you enough volume (200 users × 80 orgs = up to 16,000
  scored pairs) to sanity-check that recommendations look reasonable and that
  the dashboard charts aren't empty.
- Re-run `python database.py` any time you regenerate the CSVs to refresh the DB.
- The recommendation engine was tested standalone (`python recommender.py`) and
  produces ranked top-10 matches with score breakdowns — confirmed working.
