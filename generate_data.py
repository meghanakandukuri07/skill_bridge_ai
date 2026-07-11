"""
generate_data.py
Creates realistic sample datasets for the platform so you can test
the recommendation engine before hooking up real registrations.
Run: python generate_data.py
"""

import random
import pandas as pd
from datetime import datetime, timedelta

random.seed(42)

SKILLS_POOL = [
    "Python", "Data Analysis", "Machine Learning", "SQL", "Excel",
    "Web Development", "JavaScript", "React", "Public Speaking",
    "Content Writing", "Graphic Design", "Social Media Marketing",
    "Teaching", "Community Outreach", "Fundraising", "Event Management",
    "Java", "C++", "Data Visualization", "Project Management",
    "Video Editing", "Photography", "Research", "First Aid",
]

INTERESTS_POOL = [
    "Education", "Healthcare", "Environment", "Technology", "Women Empowerment",
    "Child Welfare", "Animal Welfare", "Disaster Relief", "Rural Development",
    "Human Rights", "Arts & Culture", "Sports", "Data Science", "Startups",
]

DOMAINS = [
    "Education", "Healthcare", "Environment", "Technology", "Social Work",
    "Marketing", "Finance", "Design", "Research", "Community Development",
]

CITIES = [
    "Hyderabad", "Bengaluru", "Delhi", "Mumbai", "Chennai", "Pune",
    "Kolkata", "Remote",
]

EDUCATION_LEVELS = ["High School", "Undergraduate", "Postgraduate", "PhD"]
AVAILABILITY = ["Full-time", "Part-time", "Weekends", "Flexible"]
EXPERIENCE_LEVELS = ["Beginner", "Intermediate", "Experienced"]


def sample_skills(k_range=(2, 5)):
    k = random.randint(*k_range)
    return ", ".join(sorted(random.sample(SKILLS_POOL, k)))


def sample_interests(k_range=(1, 3)):
    k = random.randint(*k_range)
    return ", ".join(sorted(random.sample(INTERESTS_POOL, k)))


def generate_users(n=200):
    rows = []
    for i in range(1, n + 1):
        rows.append({
            "user_id": f"U{i:04d}",
            "name": f"User_{i}",
            "skills": sample_skills(),
            "education": random.choice(EDUCATION_LEVELS),
            "interests": sample_interests(),
            "location": random.choice(CITIES[:-1]),  # users have a real city
            "availability": random.choice(AVAILABILITY),
            "experience": random.choice(EXPERIENCE_LEVELS),
            "preferred_domain": random.choice(DOMAINS),
        })
    return pd.DataFrame(rows)


def generate_organizations(n=80):
    rows = []
    for i in range(1, n + 1):
        deadline = datetime.now() + timedelta(days=random.randint(5, 90))
        mode = random.choice(["Remote", "On-site", "Hybrid"])
        rows.append({
            "org_id": f"O{i:04d}",
            "org_name": f"Organization_{i}",
            "role": f"{random.choice(DOMAINS)} {random.choice(['Intern', 'Volunteer', 'Fellow'])}",
            "required_skills": sample_skills(),
            "domain": random.choice(DOMAINS),
            "location": random.choice(CITIES),
            "mode": mode,
            "duration_weeks": random.choice([4, 8, 12, 16, 24]),
            "eligibility": random.choice(EDUCATION_LEVELS),
            "min_experience": random.choice(EXPERIENCE_LEVELS),
            "openings": random.randint(1, 10),
            "stipend": random.choice([0, 2000, 5000, 8000, 15000]),
            "deadline": deadline.strftime("%Y-%m-%d"),
        })
    return pd.DataFrame(rows)


if __name__ == "__main__":
    users = generate_users(200)
    orgs = generate_organizations(80)
    users.to_csv("data/users.csv", index=False)
    orgs.to_csv("data/organizations.csv", index=False)
    print(f"Generated {len(users)} users -> data/users.csv")
    print(f"Generated {len(orgs)} organizations -> data/organizations.csv")
