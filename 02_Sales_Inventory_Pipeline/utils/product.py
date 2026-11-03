class Product:
    def __init__(self, name: str, price: float, quantity: int):
        self.name = name
        self.price = price
        self.quantity = quantity

    def total_value(self) -> float:
        return self.price * self.quantity

    def __str__(self) -> str:
        return f"Product({self.name}, Price={self.price:.2f}, Qty={self.quantity})"
