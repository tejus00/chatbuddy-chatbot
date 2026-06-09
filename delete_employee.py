# delete_employee.py
from app import app
from db import db
from model import Employee

with app.app_context():
    emp = Employee.query.filter_by(email="ravi@example.com").first()
    if emp:
        db.session.delete(emp)
        db.session.commit()
        print("Deleted employee id:", emp.id)
    else:
        print("No such employee")
