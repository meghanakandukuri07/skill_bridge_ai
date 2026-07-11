"""
app.py
Streamlit front-end for the AI Volunteer & Internship Matching Platform.

Run with:  streamlit run app.py
(First time: python database.py   -- to create + seed the DB)
"""

import streamlit as st
import pandas as pd
import plotly.express as px

import database as db
from recommender import generate_recommendations, clean_users, clean_organizations

st.set_page_config(page_title="AI Volunteer & Internship Matcher", layout="wide")
db.init_db()

# ---------------------------------------------------------------
# Sidebar navigation
# ---------------------------------------------------------------
page = st.sidebar.radio(
    "Navigate",
    ["🏠 Home", "🧑 User Registration", "🏢 Organization Registration",
     "🎯 Recommendations", "📊 Dashboard"],
)

st.sidebar.markdown("---")
st.sidebar.caption("AI Volunteer & Internship Matching Platform — prototype")


def load_data():
    users = db.fetch_df("users")
    orgs = db.fetch_df("organizations")
    return users, orgs


# ---------------------------------------------------------------
# HOME
# ---------------------------------------------------------------
if page == "🏠 Home":
    st.title("🤝 AI Volunteer & Internship Matching Platform")
    st.write(
        "This prototype matches students/professionals with internships, NGO "
        "projects, and volunteer programs using a content-based AI recommendation "
        "engine (TF-IDF + cosine similarity + rule-based scoring)."
    )
    users, orgs = load_data()
    col1, col2, col3 = st.columns(3)
    col1.metric("Registered Users", len(users))
    col2.metric("Active Opportunities", len(orgs))
    col3.metric("Applications Logged", len(db.fetch_df("applications")))
    st.info("Use the sidebar to register a user/organization, get recommendations, or explore the analytics dashboard.")

# ---------------------------------------------------------------
# USER REGISTRATION
# ---------------------------------------------------------------
elif page == "🧑 User Registration":
    st.title("🧑 User Registration")
    with st.form("user_form"):
        user_id = st.text_input("User ID (unique)", value="")
        name = st.text_input("Full Name")
        skills = st.text_input("Skills (comma-separated)", placeholder="Python, SQL, Data Analysis")
        education = st.selectbox("Education", ["High School", "Undergraduate", "Postgraduate", "PhD"])
        interests = st.text_input("Interests (comma-separated)", placeholder="Education, Technology")
        location = st.text_input("Location", placeholder="Hyderabad")
        availability = st.selectbox("Availability", ["Full-time", "Part-time", "Weekends", "Flexible"])
        experience = st.selectbox("Experience Level", ["Beginner", "Intermediate", "Experienced"])
        preferred_domain = st.text_input("Preferred Domain", placeholder="Technology")
        submitted = st.form_submit_button("Register")

    if submitted:
        if not user_id or not name:
            st.error("User ID and Name are required.")
        else:
            db.add_user({
                "user_id": user_id, "name": name, "skills": skills, "education": education,
                "interests": interests, "location": location, "availability": availability,
                "experience": experience, "preferred_domain": preferred_domain,
            })
            st.success(f"Registered {name} ({user_id}). Head to Recommendations to see matches.")

# ---------------------------------------------------------------
# ORGANIZATION REGISTRATION
# ---------------------------------------------------------------
elif page == "🏢 Organization Registration":
    st.title("🏢 Organization Registration")
    with st.form("org_form"):
        org_id = st.text_input("Organization ID (unique)")
        org_name = st.text_input("Organization Name")
        role = st.text_input("Role Title", placeholder="Data Science Intern")
        required_skills = st.text_input("Required Skills (comma-separated)", placeholder="Python, Machine Learning")
        domain = st.text_input("Domain", placeholder="Technology")
        location = st.text_input("Location", placeholder="Bengaluru or Remote")
        mode = st.selectbox("Mode", ["Remote", "On-site", "Hybrid"])
        duration_weeks = st.number_input("Duration (weeks)", min_value=1, max_value=52, value=8)
        eligibility = st.selectbox("Minimum Eligibility", ["High School", "Undergraduate", "Postgraduate", "PhD"])
        min_experience = st.selectbox("Minimum Experience", ["Beginner", "Intermediate", "Experienced"])
        openings = st.number_input("Number of Openings", min_value=1, value=1)
        stipend = st.number_input("Stipend (0 if unpaid/volunteer)", min_value=0, value=0)
        deadline = st.date_input("Application Deadline")
        submitted = st.form_submit_button("Post Opportunity")

    if submitted:
        if not org_id or not org_name:
            st.error("Organization ID and Name are required.")
        else:
            db.add_organization({
                "org_id": org_id, "org_name": org_name, "role": role,
                "required_skills": required_skills, "domain": domain, "location": location,
                "mode": mode, "duration_weeks": duration_weeks, "eligibility": eligibility,
                "min_experience": min_experience, "openings": openings, "stipend": stipend,
                "deadline": deadline.strftime("%Y-%m-%d"),
            })
            st.success(f"Posted opportunity: {role} at {org_name}.")

# ---------------------------------------------------------------
# RECOMMENDATIONS
# ---------------------------------------------------------------
elif page == "🎯 Recommendations":
    st.title("🎯 Recommended Opportunities")
    users, orgs = load_data()
    if users.empty or orgs.empty:
        st.warning("No users or organizations yet. Register some, or run `python database.py` to load sample data.")
    else:
        selected_user = st.selectbox("Select a user", users["user_id"] + " — " + users["name"])
        user_id = selected_user.split(" — ")[0]

        top_n = st.slider("Number of recommendations", 5, 20, 10)
        if st.button("Get Recommendations"):
            with st.spinner("Scoring opportunities..."):
                recs_all = generate_recommendations(
                    users[users.user_id == user_id], orgs, top_n=top_n
                )
            if recs_all.empty:
                st.warning("No matching opportunities found (check that deadlines haven't passed).")
            else:
                st.session_state["recs"] = recs_all

        if "recs" in st.session_state:
            recs = st.session_state["recs"]
            for _, row in recs.iterrows():
                with st.container(border=True):
                    c1, c2 = st.columns([4, 1])
                    with c1:
                        st.subheader(f"{row['role']} — {row['org_name']}")
                        st.caption(f"{row['location']} · {row['mode']} · Stipend: ₹{row['stipend']} · Deadline: {row['deadline']}")
                    with c2:
                        st.metric("Match Score", f"{row['match_score']}%")
                    if st.button(f"Apply to {row['org_id']}", key=f"apply_{row['org_id']}"):
                        db.add_application(user_id, row["org_id"], row["match_score"])
                        st.success("Application recorded!")

# ---------------------------------------------------------------
# DASHBOARD
# ---------------------------------------------------------------
elif page == "📊 Dashboard":
    st.title("📊 Analytics Dashboard")
    users, orgs = load_data()
    apps = db.fetch_df("applications")

    if orgs.empty:
        st.warning("No opportunity data yet.")
    else:
        orgs_clean = clean_organizations(orgs)
        users_clean = clean_users(users) if not users.empty else users

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Most In-Demand Skills (from Opportunities)")
            skill_series = orgs_clean["required_skills"].str.split(", ").explode()
            skill_counts = skill_series.value_counts().head(10).reset_index()
            skill_counts.columns = ["skill", "count"]
            fig = px.bar(skill_counts, x="count", y="skill", orientation="h")
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Opportunities by Domain")
            domain_counts = orgs_clean["domain"].value_counts().reset_index()
            domain_counts.columns = ["domain", "count"]
            fig2 = px.pie(domain_counts, names="domain", values="count")
            st.plotly_chart(fig2, use_container_width=True)

        col3, col4 = st.columns(2)

        with col3:
            st.subheader("Volunteer/Internship Demand by Location")
            loc_counts = orgs_clean["location"].value_counts().reset_index()
            loc_counts.columns = ["location", "count"]
            fig3 = px.bar(loc_counts, x="location", y="count")
            st.plotly_chart(fig3, use_container_width=True)

        with col4:
            st.subheader("Applications Logged Over Time")
            if not apps.empty:
                apps["applied_date"] = pd.to_datetime(apps["applied_date"]).dt.date
                daily = apps.groupby("applied_date").size().reset_index(name="count")
                fig4 = px.line(daily, x="applied_date", y="count", markers=True)
                st.plotly_chart(fig4, use_container_width=True)
            else:
                st.info("No applications logged yet.")

        if not users_clean.empty:
            st.subheader("Skill Gap Analysis: User Skills vs Opportunity Requirements")
            user_skills = set(users_clean["skills"].str.split(", ").explode().dropna()) - {""}
            org_skills = set(orgs_clean["required_skills"].str.split(", ").explode().dropna()) - {""}
            gap = sorted(org_skills - user_skills)
            covered = sorted(org_skills & user_skills)
            gcol1, gcol2 = st.columns(2)
            gcol1.metric("Skills covered by user pool", len(covered))
            gcol2.metric("Skills in demand but missing", len(gap))
            if gap:
                st.write("Missing skills organizations need but users don't have (upskilling opportunities):")
                st.write(", ".join(gap))
