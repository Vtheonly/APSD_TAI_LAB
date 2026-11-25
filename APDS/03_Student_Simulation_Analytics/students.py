import random
import datetime

def generate_random_birthdate(start_year: int = 2000, end_year: int = 2006) -> datetime.date:
    start_date = datetime.date(start_year, 1, 1)
    end_date = datetime.date(end_year, 12, 31)
    delta_days = (end_date - start_date).days
    random_days = random.randint(0, delta_days)
    return start_date + datetime.timedelta(days=random_days)

def generate_students(num_students: int = 10, seed: int = 42) -> list:
    random.seed(seed)
    students = []
    for i in range(1, num_students + 1):
        students.append({
            "student_id": f"STU_{i:03d}",
            "birthdate": generate_random_birthdate(2000, 2006),
            "grades": [round(random.uniform(0.0, 20.0), 2) for _ in range(3)]
        })
    return students
