from database import db


class User(db.Model):

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)
    name3 = db.Column(db.String(3), nullable=False)

    birthtime = db.Column(db.String(10))
    birthplace = db.Column(db.String(100))

    phone = db.Column(db.String(20), unique=True, nullable=False)

    age = db.Column(db.Integer)
    height = db.Column(db.String(10))
    profession = db.Column(db.String(100))
    location = db.Column(db.String(100))

    subscription_active = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"<User {self.name}>"



class Agent(db.Model):

    __tablename__ = "agents"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    password_hash = db.Column(db.String(200), nullable=False)

    def __repr__(self):
        return f"<Agent {self.email}>"