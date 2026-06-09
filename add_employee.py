# add_employee.py
from app import app
from db import db
from model import Employee

with app.app_context():
    email = "ravi@example.com"
    existing = Employee.query.filter_by(email=email).first()
    if existing:
        print("Email already exists, id:", existing.id)
    else:
        emp = Employee(
            name="Ravi",
            email=email,
            department="HR",
            designation="Manager",
            salary=45000
        )
        db.session.add(emp)
        db.session.commit()
        print("Inserted employee with ID:", emp.id)
