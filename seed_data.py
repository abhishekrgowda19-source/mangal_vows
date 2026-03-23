import os
from dotenv import load_dotenv
load_dotenv()

from app import app, bcrypt
from database import db
from models import User, Agent
from datetime import datetime, timedelta


# ─────────────────────────────────────────
# 4 AGENTS
# ─────────────────────────────────────────

agents_data = [
    {"name": "Ravi Kumar",   "email": "ravi@mangalvows.com",   "phone": "9000000001", "password": "agent123"},
    {"name": "Priya Sharma", "email": "priya@mangalvows.com",  "phone": "9000000002", "password": "agent123"},
    {"name": "Suresh Nair",  "email": "suresh@mangalvows.com", "phone": "9000000003", "password": "agent123"},
    {"name": "Anita Reddy",  "email": "anita@mangalvows.com",  "phone": "9000000004", "password": "agent123"},
]


# ─────────────────────────────────────────
# 40 USERS (20 Male + 20 Female) WITH CASTE
# ─────────────────────────────────────────

users_data = [

    # ── MALE USERS ──────────────────────────────────────────────────────────
    {"name": "Arjun Sharma",    "phone": "9100000001", "gender": "Male",   "age": 28, "height": "5'10", "profession": "Software Engineer",     "education": "B.Tech",       "city": "Bangalore",  "state": "Karnataka",     "religion": "Hindu",  "caste": "Brahmin",   "community": "Brahmin",  "mother_tongue": "Kannada"},
    {"name": "Kiran Patel",     "phone": "9100000002", "gender": "Male",   "age": 30, "height": "5'9",  "profession": "Doctor",                "education": "MBBS",         "city": "Ahmedabad",  "state": "Gujarat",       "religion": "Hindu",  "caste": "Patel",     "community": "Patel",    "mother_tongue": "Gujarati"},
    {"name": "Rahul Verma",     "phone": "9100000003", "gender": "Male",   "age": 27, "height": "5'8",  "profession": "Chartered Accountant",  "education": "CA",           "city": "Delhi",      "state": "Delhi",         "religion": "Hindu",  "caste": "Vaishya",   "community": "Vaishya",  "mother_tongue": "Hindi"},
    {"name": "Sanjay Iyer",     "phone": "9100000004", "gender": "Male",   "age": 32, "height": "5'11", "profession": "Business Owner",        "education": "MBA",          "city": "Chennai",    "state": "Tamil Nadu",    "religion": "Hindu",  "caste": "Brahmin",   "community": "Iyer",     "mother_tongue": "Tamil"},
    {"name": "Mohammed Rizwan", "phone": "9100000005", "gender": "Male",   "age": 29, "height": "5'9",  "profession": "Engineer",              "education": "B.Tech",       "city": "Hyderabad",  "state": "Telangana",     "religion": "Muslim", "caste": "Sunni",     "community": "Sunni",    "mother_tongue": "Urdu"},
    {"name": "Vikram Singh",    "phone": "9100000006", "gender": "Male",   "age": 31, "height": "6'0",  "profession": "Army Officer",          "education": "B.Sc",         "city": "Jaipur",     "state": "Rajasthan",     "religion": "Hindu",  "caste": "Rajput",    "community": "Rajput",   "mother_tongue": "Hindi"},
    {"name": "Anil Desai",      "phone": "9100000007", "gender": "Male",   "age": 26, "height": "5'8",  "profession": "Architect",             "education": "B.Arch",       "city": "Pune",       "state": "Maharashtra",   "religion": "Hindu",  "caste": "Maratha",   "community": "Maratha",  "mother_tongue": "Marathi"},
    {"name": "Deepak Nair",     "phone": "9100000008", "gender": "Male",   "age": 33, "height": "5'10", "profession": "Lawyer",                "education": "LLB",          "city": "Kochi",      "state": "Kerala",        "religion": "Hindu",  "caste": "Nair",      "community": "Nair",     "mother_tongue": "Malayalam"},
    {"name": "Sunil Gupta",     "phone": "9100000009", "gender": "Male",   "age": 28, "height": "5'7",  "profession": "Banker",                "education": "MBA",          "city": "Mumbai",     "state": "Maharashtra",   "religion": "Hindu",  "caste": "Gupta",     "community": "Gupta",    "mother_tongue": "Hindi"},
    {"name": "Harish Reddy",    "phone": "9100000010", "gender": "Male",   "age": 30, "height": "5'9",  "profession": "Data Scientist",        "education": "M.Tech",       "city": "Hyderabad",  "state": "Telangana",     "religion": "Hindu",  "caste": "Reddy",     "community": "Reddy",    "mother_tongue": "Telugu"},
    {"name": "Amit Joshi",      "phone": "9100000011", "gender": "Male",   "age": 27, "height": "5'8",  "profession": "Teacher",               "education": "M.Ed",         "city": "Nashik",     "state": "Maharashtra",   "religion": "Hindu",  "caste": "Brahmin",   "community": "Brahmin",  "mother_tongue": "Marathi"},
    {"name": "Rajesh Kumar",    "phone": "9100000012", "gender": "Male",   "age": 35, "height": "5'7",  "profession": "Pharmacist",            "education": "B.Pharma",     "city": "Lucknow",    "state": "Uttar Pradesh", "religion": "Hindu",  "caste": "Kayastha",  "community": "Kayastha", "mother_tongue": "Hindi"},
    {"name": "Naveen Gowda",    "phone": "9100000013", "gender": "Male",   "age": 29, "height": "5'9",  "profession": "Civil Engineer",        "education": "B.Tech",       "city": "Mysore",     "state": "Karnataka",     "religion": "Hindu",  "caste": "Vokkaliga", "community": "Vokkaliga","mother_tongue": "Kannada"},
    {"name": "Farhan Sheikh",   "phone": "9100000014", "gender": "Male",   "age": 28, "height": "5'8",  "profession": "Graphic Designer",      "education": "B.Des",        "city": "Pune",       "state": "Maharashtra",   "religion": "Muslim", "caste": "Sunni",     "community": "Sunni",    "mother_tongue": "Urdu"},
    {"name": "Praveen Menon",   "phone": "9100000015", "gender": "Male",   "age": 31, "height": "5'11", "profession": "Pilot",                 "education": "B.Sc Aviation","city": "Kochi",      "state": "Kerala",        "religion": "Hindu",  "caste": "Menon",     "community": "Menon",    "mother_tongue": "Malayalam"},
    {"name": "Gaurav Tiwari",   "phone": "9100000016", "gender": "Male",   "age": 26, "height": "5'8",  "profession": "Journalist",            "education": "BA",           "city": "Bhopal",     "state": "Madhya Pradesh","religion": "Hindu",  "caste": "Brahmin",   "community": "Brahmin",  "mother_tongue": "Hindi"},
    {"name": "Santosh Pillai",  "phone": "9100000017", "gender": "Male",   "age": 34, "height": "5'10", "profession": "Professor",             "education": "PhD",          "city": "Trivandrum", "state": "Kerala",        "religion": "Hindu",  "caste": "Pillai",    "community": "Pillai",   "mother_tongue": "Malayalam"},
    {"name": "Rohit Malhotra",  "phone": "9100000018", "gender": "Male",   "age": 29, "height": "5'9",  "profession": "Product Manager",       "education": "MBA",          "city": "Gurgaon",    "state": "Haryana",       "religion": "Hindu",  "caste": "Khatri",    "community": "Khatri",   "mother_tongue": "Punjabi"},
    {"name": "Kartik Bhat",     "phone": "9100000019", "gender": "Male",   "age": 27, "height": "5'8",  "profession": "Startup Founder",       "education": "B.Tech",       "city": "Bangalore",  "state": "Karnataka",     "religion": "Hindu",  "caste": "Brahmin",   "community": "Brahmin",  "mother_tongue": "Kannada"},
    {"name": "Imran Khan",      "phone": "9100000020", "gender": "Male",   "age": 30, "height": "5'10", "profession": "Sales Manager",         "education": "BBA",          "city": "Nagpur",     "state": "Maharashtra",   "religion": "Muslim", "caste": "Pathan",    "community": "Sunni",    "mother_tongue": "Urdu"},

    # ── FEMALE USERS ────────────────────────────────────────────────────────
    {"name": "Priya Sharma",    "phone": "9200000001", "gender": "Female", "age": 25, "height": "5'4",  "profession": "Software Engineer",     "education": "B.Tech",       "city": "Bangalore",  "state": "Karnataka",     "religion": "Hindu",  "caste": "Brahmin",   "community": "Brahmin",  "mother_tongue": "Hindi"},
    {"name": "Sneha Patel",     "phone": "9200000002", "gender": "Female", "age": 27, "height": "5'3",  "profession": "Doctor",                "education": "MBBS",         "city": "Surat",      "state": "Gujarat",       "religion": "Hindu",  "caste": "Patel",     "community": "Patel",    "mother_tongue": "Gujarati"},
    {"name": "Ananya Iyer",     "phone": "9200000003", "gender": "Female", "age": 24, "height": "5'3",  "profession": "Teacher",               "education": "B.Ed",         "city": "Chennai",    "state": "Tamil Nadu",    "religion": "Hindu",  "caste": "Brahmin",   "community": "Iyer",     "mother_tongue": "Tamil"},
    {"name": "Divya Nair",      "phone": "9200000004", "gender": "Female", "age": 26, "height": "5'4",  "profession": "Nurse",                 "education": "B.Sc Nursing", "city": "Kochi",      "state": "Kerala",        "religion": "Hindu",  "caste": "Nair",      "community": "Nair",     "mother_tongue": "Malayalam"},
    {"name": "Fatima Shaikh",   "phone": "9200000005", "gender": "Female", "age": 25, "height": "5'4",  "profession": "Fashion Designer",      "education": "B.Des",        "city": "Mumbai",     "state": "Maharashtra",   "religion": "Muslim", "caste": "Sunni",     "community": "Sunni",    "mother_tongue": "Urdu"},
    {"name": "Kavya Reddy",     "phone": "9200000006", "gender": "Female", "age": 28, "height": "5'5",  "profession": "Banker",                "education": "MBA",          "city": "Hyderabad",  "state": "Telangana",     "religion": "Hindu",  "caste": "Reddy",     "community": "Reddy",    "mother_tongue": "Telugu"},
    {"name": "Meera Joshi",     "phone": "9200000007", "gender": "Female", "age": 26, "height": "5'3",  "profession": "Lawyer",                "education": "LLB",          "city": "Pune",       "state": "Maharashtra",   "religion": "Hindu",  "caste": "Brahmin",   "community": "Brahmin",  "mother_tongue": "Marathi"},
    {"name": "Pooja Gupta",     "phone": "9200000008", "gender": "Female", "age": 23, "height": "5'2",  "profession": "Graphic Designer",      "education": "B.Des",        "city": "Delhi",      "state": "Delhi",         "religion": "Hindu",  "caste": "Gupta",     "community": "Gupta",    "mother_tongue": "Hindi"},
    {"name": "Riya Singh",      "phone": "9200000009", "gender": "Female", "age": 27, "height": "5'4",  "profession": "Chartered Accountant",  "education": "CA",           "city": "Jaipur",     "state": "Rajasthan",     "religion": "Hindu",  "caste": "Rajput",    "community": "Rajput",   "mother_tongue": "Hindi"},
    {"name": "Lakshmi Menon",   "phone": "9200000010", "gender": "Female", "age": 29, "height": "5'5",  "profession": "Professor",             "education": "M.Sc",         "city": "Trivandrum", "state": "Kerala",        "religion": "Hindu",  "caste": "Menon",     "community": "Menon",    "mother_tongue": "Malayalam"},
    {"name": "Nisha Verma",     "phone": "9200000011", "gender": "Female", "age": 25, "height": "5'3",  "profession": "Data Analyst",          "education": "B.Tech",       "city": "Noida",      "state": "Uttar Pradesh", "religion": "Hindu",  "caste": "Brahmin",   "community": "Brahmin",  "mother_tongue": "Hindi"},
    {"name": "Sana Mirza",      "phone": "9200000012", "gender": "Female", "age": 26, "height": "5'4",  "profession": "Journalist",            "education": "BA",           "city": "Lucknow",    "state": "Uttar Pradesh", "religion": "Muslim", "caste": "Sunni",     "community": "Sunni",    "mother_tongue": "Urdu"},
    {"name": "Deepika Gowda",   "phone": "9200000013", "gender": "Female", "age": 24, "height": "5'3",  "profession": "Architect",             "education": "B.Arch",       "city": "Mysore",     "state": "Karnataka",     "religion": "Hindu",  "caste": "Vokkaliga", "community": "Vokkaliga","mother_tongue": "Kannada"},
    {"name": "Anjali Desai",    "phone": "9200000014", "gender": "Female", "age": 28, "height": "5'4",  "profession": "Pharmacist",            "education": "B.Pharma",     "city": "Vadodara",   "state": "Gujarat",       "religion": "Hindu",  "caste": "Brahmin",   "community": "Brahmin",  "mother_tongue": "Gujarati"},
    {"name": "Swathi Pillai",   "phone": "9200000015", "gender": "Female", "age": 27, "height": "5'4",  "profession": "Civil Engineer",        "education": "B.Tech",       "city": "Kochi",      "state": "Kerala",        "religion": "Hindu",  "caste": "Pillai",    "community": "Pillai",   "mother_tongue": "Malayalam"},
    {"name": "Radhika Malhotra","phone": "9200000016", "gender": "Female", "age": 25, "height": "5'3",  "profession": "HR Manager",            "education": "MBA",          "city": "Gurgaon",    "state": "Haryana",       "religion": "Hindu",  "caste": "Khatri",    "community": "Khatri",   "mother_tongue": "Punjabi"},
    {"name": "Bhavna Tiwari",   "phone": "9200000017", "gender": "Female", "age": 26, "height": "5'2",  "profession": "Content Writer",        "education": "BA",           "city": "Bhopal",     "state": "Madhya Pradesh","religion": "Hindu",  "caste": "Brahmin",   "community": "Brahmin",  "mother_tongue": "Hindi"},
    {"name": "Shruti Bhat",     "phone": "9200000018", "gender": "Female", "age": 24, "height": "5'3",  "profession": "UX Designer",           "education": "B.Des",        "city": "Bangalore",  "state": "Karnataka",     "religion": "Hindu",  "caste": "Brahmin",   "community": "Brahmin",  "mother_tongue": "Kannada"},
    {"name": "Zara Khan",       "phone": "9200000019", "gender": "Female", "age": 27, "height": "5'4",  "profession": "Dentist",               "education": "BDS",          "city": "Nagpur",     "state": "Maharashtra",   "religion": "Muslim", "caste": "Pathan",    "community": "Sunni",    "mother_tongue": "Urdu"},
    {"name": "Harini Krishnan", "phone": "9200000020", "gender": "Female", "age": 25, "height": "5'3",  "profession": "Software Engineer",     "education": "B.Tech",       "city": "Chennai",    "state": "Tamil Nadu",    "religion": "Hindu",  "caste": "Brahmin",   "community": "Brahmin",  "mother_tongue": "Tamil"},
]


# ─────────────────────────────────────────
# INSERT INTO DATABASE
# ─────────────────────────────────────────

with app.app_context():

    inserted_agents = []

    print("=" * 55)
    print("   MANGAL VOWS — SEED DATA")
    print("=" * 55)

    # Insert Agents
    print("\n📋 Adding Agents...")
    for a in agents_data:
        if not Agent.query.filter_by(email=a["email"]).first():
            agent = Agent(
                name          = a["name"],
                email         = a["email"],
                phone         = a["phone"],
                password_hash = bcrypt.generate_password_hash(a["password"]).decode("utf-8"),
                is_active     = True
            )
            db.session.add(agent)
            db.session.flush()
            inserted_agents.append(agent)
            print(f"  ✅ {a['name']} | {a['email']} | Password: {a['password']}")
        else:
            existing = Agent.query.filter_by(email=a["email"]).first()
            inserted_agents.append(existing)
            print(f"  ⚠️  Already exists: {a['email']}")

    db.session.commit()

    # Insert Users
    print("\n👥 Adding Users...")
    for i, u in enumerate(users_data):
        if not User.query.filter_by(phone=u["phone"]).first():
            agent = inserted_agents[i % len(inserted_agents)]
            new_user = User(
                name                = u["name"],
                phone               = u["phone"],
                gender              = u["gender"],
                age                 = u["age"],
                height              = u["height"],
                profession          = u["profession"],
                education           = u["education"],
                city                = u["city"],
                state               = u["state"],
                location            = f"{u['city']}, {u['state']}",
                religion            = u["religion"],
                caste               = u["caste"],
                community           = u["community"],
                mother_tongue       = u["mother_tongue"],
                agent_id            = agent.id,
                subscription_active = True,
                subscription_expiry = datetime.utcnow() + timedelta(days=30)
            )
            db.session.add(new_user)
            print(f"  ✅ {u['name']:<20} | {u['gender']:<7} | {u['caste']:<12} | {u['city']}")
        else:
            print(f"  ⚠️  Already exists: {u['phone']}")

    db.session.commit()

    print("\n" + "=" * 55)
    print("  🎉 DONE! 4 agents + 40 users added!")
    print("=" * 55)
    print("\n📋 AGENT LOGIN CREDENTIALS:")
    print("  ravi@mangalvows.com   → agent123")
    print("  priya@mangalvows.com  → agent123")
    print("  suresh@mangalvows.com → agent123")
    print("  anita@mangalvows.com  → agent123")
    print("\n📋 SAMPLE USER LOGIN (Commercial):")
    print("  Name3: ARJ | Phone: 9100000001  → Arjun Sharma (Brahmin)")
    print("  Name3: KIR | Phone: 9100000002  → Kiran Patel  (Patel)")
    print("  Name3: PRI | Phone: 9200000001  → Priya Sharma (Brahmin)")
    print("  Name3: SNE | Phone: 9200000002  → Sneha Patel  (Patel)")
    print("=" * 55)