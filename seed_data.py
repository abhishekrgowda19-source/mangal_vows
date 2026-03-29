import os
import random
from dotenv import load_dotenv
load_dotenv()

from app import app
from database import db, bcrypt
from models import User, Agent
from datetime import datetime, timedelta


# ─────────────────────────────────────────
# AGENTS DATA
# ─────────────────────────────────────────
agents_data = [
    {"name": "Ravi Kumar",   "email": "ravi@mangalvows.com",   "phone": "9000000001", "password": "agent123"},
    {"name": "Priya Sharma", "email": "priya@mangalvows.com",  "phone": "9000000002", "password": "agent123"},
    {"name": "Suresh Nair",  "email": "suresh@mangalvows.com", "phone": "9000000003", "password": "agent123"},
    {"name": "Anita Reddy",  "email": "anita@mangalvows.com",  "phone": "9000000004", "password": "agent123"},
]


# ─────────────────────────────────────────
# REALISTIC USER GENERATOR
# ─────────────────────────────────────────
def generate_users():
    first_names_male   = ["Arjun", "Rahul", "Karthik", "Vikram", "Rohit", "Manoj", "Siddharth", "Nikhil"]
    first_names_female = ["Ananya", "Pooja", "Sneha", "Kavya", "Divya", "Neha", "Aishwarya", "Ritu"]

    email_domains = ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "rediffmail.com"]

    cities = [
        ("Bangalore", "Karnataka"),
        ("Mysore", "Karnataka"),
        ("Chennai", "Tamil Nadu"),
        ("Hyderabad", "Telangana"),
        ("Pune", "Maharashtra"),
        ("Mumbai", "Maharashtra"),
        ("Delhi", "Delhi"),
        ("Ahmedabad", "Gujarat"),
        ("Kochi", "Kerala"),
        ("Jaipur", "Rajasthan")
    ]

    professions = [
        ("Software Engineer", "B.Tech"),
        ("Doctor", "MBBS"),
        ("Teacher", "B.Ed"),
        ("Bank Manager", "MBA"),
        ("Business Owner", "B.Com"),
        ("Civil Engineer", "B.Tech"),
        ("Designer", "B.Des"),
        ("Lawyer", "LLB")
    ]

    religions  = ["Hindu", "Muslim", "Christian"]
    castes     = ["General", "OBC", "SC", "ST"]
    languages  = ["Kannada", "Tamil", "Hindi", "Telugu", "Malayalam", "Marathi"]

    users = []

    for i in range(40):
        gender            = "Male" if i < 20 else "Female"
        name              = random.choice(first_names_male if gender == "Male" else first_names_female)
        city, state       = random.choice(cities)
        profession, education = random.choice(professions)

        phone = f"9{random.randint(100000000, 999999999)}"
        email = f"{name.lower()}{i}@{random.choice(email_domains)}"

        users.append({
            "name":          f"{name}{i}",
            "phone":         phone,
            "email":         email,
            "gender":        gender,
            "age":           random.randint(23, 35),
            "height":        f"{random.randint(150, 185)} cm",
            "profession":    profession,
            "education":     education,
            "city":          city,
            "state":         state,
            "religion":      random.choice(religions),
            "caste":         random.choice(castes),
            "community":     random.choice(castes),
            "mother_tongue": random.choice(languages),
        })

    return users


# ─────────────────────────────────────────
# BIRTH TIME GENERATOR — normalized format
# ─────────────────────────────────────────
def generate_birth_time():
    hour   = random.randint(1, 12)
    minute = random.randint(0, 59)
    period = random.choice(["AM", "PM"])
    return f"{hour}:{minute:02d} {period}"   # e.g. "5:03 AM", "11:45 PM"


# ─────────────────────────────────────────
# RUN SEED
# ─────────────────────────────────────────
with app.app_context():

    print("\n🚀 STARTING SEED...\n")

    # CLEAR OLD DATA
    User.query.delete()
    Agent.query.delete()
    db.session.commit()

    inserted_agents = []

    # INSERT AGENTS
    for a in agents_data:
        agent = Agent(
            name=a["name"],
            email=a["email"],
            phone=a["phone"],
            password_hash=bcrypt.generate_password_hash(a["password"]).decode("utf-8"),
            is_active=True
        )
        db.session.add(agent)
        db.session.flush()
        inserted_agents.append(agent)

    db.session.commit()
    print("✅ Agents inserted")

    users_data = generate_users()

    # INSERT USERS
    for i, u in enumerate(users_data):

        agent         = inserted_agents[i % len(inserted_agents)]
        is_subscribed = random.choice([True, False])

        # ✅ Only set expiry/started if subscribed
        expiry  = datetime.utcnow() + timedelta(days=random.randint(10, 60)) if is_subscribed else None
        started = datetime.utcnow() - timedelta(days=random.randint(30, 90)) if is_subscribed else None

        new_user = User(
            name          = u["name"],
            phone         = u["phone"],
            email         = u["email"],
            gender        = u["gender"],
            age           = u["age"],
            height        = u["height"],
            profession    = u["profession"],
            education     = u["education"],
            city          = u["city"],
            state         = u["state"],
            location      = f"{u['city']}, {u['state']}",
            religion      = u["religion"],
            caste         = u["caste"],
            community     = u["community"],
            mother_tongue = u["mother_tongue"],

            # ✅ ALL users are personal — they are real profiles with credentials
            user_type   = "personal",
            birth_place = u["city"],
            birth_time  = generate_birth_time(),

            agent_id             = agent.id,
            subscription_active  = is_subscribed,
            subscription_expiry  = expiry,
            subscription_started = started,
        )

        db.session.add(new_user)

    db.session.commit()

    print("\n🎉 DONE!")
    print("👉 40 PERSONAL USERS inserted (all have birth_place + birth_time credentials)")
    print("👉 4 AGENTS inserted\n")