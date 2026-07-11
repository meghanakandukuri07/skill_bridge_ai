"""
recommender.py
The core AI matching engine:
1. Preprocessing (cleaning, skill standardization)
2. TF-IDF vectorization of skills + interests/domain text
3. Cosine similarity for content-based skill/interest matching
4. Rule-based scoring for location, availability, education, experience
5. Weighted final compatibility score, ranked top-N
"""

import re
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

EXPERIENCE_RANK = {"Beginner": 1, "Intermediate": 2, "Experienced": 3}
EDUCATION_RANK = {"High School": 1, "Undergraduate": 2, "Postgraduate": 3, "PhD": 4}

# Weights for the final compatibility score — tune these based on feedback (Step 6)
WEIGHTS = {
    "skill_interest": 0.50,
    "location": 0.20,
    "availability": 0.10,
    "education": 0.10,
    "experience": 0.10,
}


# ---------- 1. Preprocessing ----------

def standardize_skill_string(raw: str) -> str:
    """Lowercase, strip, dedupe, title-case each skill so 'python' == 'Python'."""
    if pd.isna(raw) or not str(raw).strip():
        return ""
    parts = [p.strip() for p in re.split(r"[,;/]", str(raw)) if p.strip()]
    seen, cleaned = set(), []
    for p in parts:
        key = p.lower()
        if key not in seen:
            seen.add(key)
            cleaned.append(key.title() if key.upper() not in {"SQL"} else key.upper())
    return ", ".join(cleaned)


def clean_users(df: pd.DataFrame) -> pd.DataFrame:
    df = df.drop_duplicates(subset="user_id").copy()
    df["skills"] = df["skills"].apply(standardize_skill_string)
    df["interests"] = df["interests"].apply(standardize_skill_string)
    for col in ["education", "location", "availability", "experience", "preferred_domain"]:
        df[col] = df[col].fillna("Unknown").astype(str).str.strip()
    df["text_profile"] = (df["skills"] + " " + df["interests"] + " " + df["preferred_domain"])
    return df


def clean_organizations(df: pd.DataFrame) -> pd.DataFrame:
    df = df.drop_duplicates(subset="org_id").copy()
    df["required_skills"] = df["required_skills"].apply(standardize_skill_string)
    for col in ["domain", "location", "mode", "eligibility", "min_experience"]:
        df[col] = df[col].fillna("Unknown").astype(str).str.strip()
    df["deadline"] = pd.to_datetime(df["deadline"], errors="coerce")
    df = df[df["deadline"] >= pd.Timestamp.now() - pd.Timedelta(days=1)]  # drop expired
    df["text_profile"] = df["required_skills"] + " " + df["domain"] + " " + df["role"]
    return df


# ---------- 2 & 3. TF-IDF + Cosine Similarity ----------

def compute_skill_interest_similarity(users: pd.DataFrame, orgs: pd.DataFrame) -> np.ndarray:
    """Returns a (n_users x n_orgs) matrix of cosine similarity scores in [0, 1]."""
    corpus = pd.concat([users["text_profile"], orgs["text_profile"]], ignore_index=True)
    vectorizer = TfidfVectorizer(token_pattern=r"[A-Za-z0-9\+\#]+")
    tfidf = vectorizer.fit_transform(corpus)
    user_vecs = tfidf[: len(users)]
    org_vecs = tfidf[len(users):]
    return cosine_similarity(user_vecs, org_vecs)


# ---------- 4. Rule-based compatibility scores ----------

def location_score(user_loc: str, org_loc: str, org_mode: str) -> float:
    if org_mode == "Remote":
        return 1.0
    if user_loc.strip().lower() == org_loc.strip().lower():
        return 1.0
    if org_mode == "Hybrid":
        return 0.6
    return 0.2


def availability_score(user_avail: str) -> float:
    # Full-time/flexible users fit more opportunity types than strict weekend-only users
    return {"Flexible": 1.0, "Full-time": 0.9, "Part-time": 0.7, "Weekends": 0.5}.get(user_avail, 0.5)


def education_score(user_edu: str, org_min_edu: str) -> float:
    u = EDUCATION_RANK.get(user_edu, 1)
    r = EDUCATION_RANK.get(org_min_edu, 1)
    return 1.0 if u >= r else max(0.0, 1 - 0.3 * (r - u))


def experience_score(user_exp: str, org_min_exp: str) -> float:
    u = EXPERIENCE_RANK.get(user_exp, 1)
    r = EXPERIENCE_RANK.get(org_min_exp, 1)
    return 1.0 if u >= r else max(0.0, 1 - 0.35 * (r - u))


# ---------- 5. Final ranking ----------

def generate_recommendations(users: pd.DataFrame, orgs: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    users = clean_users(users)
    orgs = clean_organizations(orgs)
    if users.empty or orgs.empty:
        return pd.DataFrame()

    sim_matrix = compute_skill_interest_similarity(users, orgs)

    results = []
    for ui, user in users.reset_index(drop=True).iterrows():
        for oi, org in orgs.reset_index(drop=True).iterrows():
            scores = {
                "skill_interest": sim_matrix[ui, oi],
                "location": location_score(user["location"], org["location"], org["mode"]),
                "availability": availability_score(user["availability"]),
                "education": education_score(user["education"], org["eligibility"]),
                "experience": experience_score(user["experience"], org["min_experience"]),
            }
            final = sum(scores[k] * WEIGHTS[k] for k in WEIGHTS)
            results.append({
                "user_id": user["user_id"],
                "org_id": org["org_id"],
                "org_name": org["org_name"],
                "role": org["role"],
                "match_score": round(final * 100, 1),
                "skill_score": round(scores["skill_interest"] * 100, 1),
                "location": org["location"],
                "mode": org["mode"],
                "stipend": org["stipend"],
                "deadline": org["deadline"].strftime("%Y-%m-%d"),
            })

    all_matches = pd.DataFrame(results)
    top_matches = (
        all_matches.sort_values(["user_id", "match_score"], ascending=[True, False])
        .groupby("user_id")
        .head(top_n)
        .reset_index(drop=True)
    )
    return top_matches


if __name__ == "__main__":
    users = pd.read_csv("data/users.csv")
    orgs = pd.read_csv("data/organizations.csv")
    recs = generate_recommendations(users, orgs, top_n=10)
    recs.to_csv("data/recommendations.csv", index=False)
    print(f"Generated {len(recs)} recommendation rows -> data/recommendations.csv")
    print(recs[recs.user_id == recs.user_id.iloc[0]])
