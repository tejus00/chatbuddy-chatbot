from datetime import datetime
from model import Employee
from db import db
import re


def rule_based_reply(text):
    if not text or not text.strip():
        return "Say something so I can reply!"

    t = text.lower().strip()

    # Greetings
    if any(word in t for word in ["hi", "hello", "hey", "hiya"]):
        return "Hello! I'm your Employee Assistant."

    # Bot Info
    if "who are you" in t or "your name" in t:
        return "I'm ChatBuddy, your Employee Management Assistant."

    # Help
    if "help" in t:
        return """
Available Commands:

show employees
employee count
departments
find employee <name>

highest salary
lowest salary
average salary

current date
current time

who are you
help
"""

    # Current Time
    if "time" in t:
        return f"Current Time: {datetime.now().strftime('%H:%M:%S')}"

    # Current Date
    if "date" in t:
        return f"Today's Date: {datetime.now().strftime('%Y-%m-%d')}"

    # Show Employees
    if t in [
        "show employees",
        "get employees",
        "list employees",
        "all employees"
    ]:
        employees = Employee.query.all()

        if not employees:
            return "No employees found."

        out = "Employees:\n"

        for e in employees:
            out += (
                f"- {e.name} ({e.email}) | "
                f"{e.department} | "
                f"{e.designation} | "
                f"Salary: {e.salary}\n"
            )

        return out

    # Employee Count
    if t in [
        "employee count",
        "total employees",
        "how many employees"
    ]:
        return f"Total Employees: {Employee.query.count()}"

    # Departments
    if t in ["departments", "list departments"]:
        departments = (
            db.session.query(Employee.department)
            .distinct()
            .all()
        )

        if not departments:
            return "No departments found."

        return "Departments:\n" + "\n".join(
            f"- {d[0]}"
            for d in departments
            if d[0]
        )

    # Find Employee
    if t.startswith("find employee"):
        name = t.replace("find employee", "").strip()

        emp = Employee.query.filter(
            Employee.name.ilike(f"%{name}%")
        ).first()

        if not emp:
            return "Employee not found."

        return (
            f"ID: {emp.id}\n"
            f"Name: {emp.name}\n"
            f"Email: {emp.email}\n"
            f"Department: {emp.department}\n"
            f"Designation: {emp.designation}\n"
            f"Salary: {emp.salary}"
        )

    # Highest Salary
    if "highest salary" in t:
        emp = Employee.query.order_by(
            Employee.salary.desc()
        ).first()

        if not emp:
            return "No employee data found."

        return f"{emp.name} has the highest salary: {emp.salary}"

    # Lowest Salary
    if "lowest salary" in t:
        emp = Employee.query.order_by(
            Employee.salary.asc()
        ).first()

        if not emp:
            return "No employee data found."

        return f"{emp.name} has the lowest salary: {emp.salary}"

    # Average Salary
    if "average salary" in t:
        employees = Employee.query.all()

        if not employees:
            return "No employee data found."

        avg = (
            sum(e.salary for e in employees if e.salary)
            / len(employees)
        )

        return f"Average Salary: {avg:.2f}"

    # Calculator
    if re.match(r'^\s*\d+\s*[\+\-\*\/]\s*\d+\s*$', text):
        try:
            return f"Result: {eval(text)}"
        except Exception:
            return "Calculation error."

    return None