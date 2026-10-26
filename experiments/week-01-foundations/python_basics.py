
# Week 01 — Python Fundamentals
# Synthetic inventory data for learning purposes.

inventory = [
    {"sku": "SRV-001", "name": "Demo Server", "qty": 5, "price": 450},
    {"sku": "SSD-002", "name": "Demo SSD", "qty": 20, "price": 35},
    {"sku": "RAM-003", "name": "Demo RAM", "qty": 12, "price": 25},
]

def calculate_inventory_value(items):
    total = 0

    for item in items:
        total += item["qty"] * item["price"]

    return total


def find_product(items, sku):
    for item in items:
        if item["sku"] == sku:
            return item

    return None


def create_quote(items, sku, quantity):
    product = find_product(items, sku)

    if product is None:
        raise ValueError("Product not found")

    if quantity <= 0:
        raise ValueError("Quantity must be positive")

    if quantity > product["qty"]:
        raise ValueError("Insufficient stock")

    return {
        "sku": sku,
        "quantity": quantity,
        "unit_price": product["price"],
        "total": quantity * product["price"],
    }


if __name__ == "__main__":
    print("Inventory value:", calculate_inventory_value(inventory))

    try:
        quote = create_quote(inventory, "SRV-001", 2)
        print("Quotation:", quote)
    except ValueError as error:
        print("Error:", error)
