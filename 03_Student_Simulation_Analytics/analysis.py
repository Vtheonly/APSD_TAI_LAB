import statistics

def calculate_age(birthdate, reference_year: int = 2026) -> int:
    return reference_year - birthdate.year

def enrich_student_data(students: list, reference_year: int = 2026) -> list:
    for s in students:
        s["age"] = calculate_age(s["birthdate"], reference_year)
        s["average"] = round(statistics.mean(s["grades"]), 2)
    return students

def compute_cohort_statistics(students: list) -> dict:
    averages = [s["average"] for s in students]
    ages = [s["age"] for s in students]
    return {
        "mean": round(statistics.mean(averages), 2),
        "median": round(statistics.median(averages), 2),
        "stdev": round(statistics.stdev(averages), 2),
        "min_average": round(min(averages), 2),
        "max_average": round(max(averages), 2),
        "mean_age": round(statistics.mean(ages), 1)
    }
