import numpy as np

def generate_random_sales(min_val: int, max_val: int, size: int) -> np.ndarray:
    return np.random.randint(low=min_val, high=max_val + 1, size=size)
