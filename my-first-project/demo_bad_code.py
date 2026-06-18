
import time
from typing import List, Dict, Any, Optional

def get_user_data(users: List[Dict[str, Any]], user_id: int) -> Optional[Dict[str, Any]]:
    """Finds a user by ID in O(N) time.
    
    In a real application, consider storing users in a dict mapping id -> user
    to achieve O(1) lookups.
    """
    for user in users:
        if user.get('id') == user_id:
            return user
    return None

def process_payments(items: List[Dict[str, Any]]) -> float:
    """Calculates total price including a 10% tax.
    
    Simulates a network delay for each item.
    """
    total = 0.0
    for item in items:
        # Avoid KeyError by using .get() with a default value
        price = item.get('price', 0.0)
        tax = price * 0.1
        total += price + tax
        
        # Simulate network latency
        time.sleep(0.1) 
  
    return total

def run_batch() -> None:
    users = [{'id': 1, 'name': 'Alice'}, {'id': 2, 'name': 'Bob'}]
    items = [{'price': 10}, {'price': 20}, {'price': 100}]
  
    # Safe handling of missing user data
    user = get_user_data(users, 3)
    if user:
        print(f"User found: {user['name']}")
    else:
        print("User not found.")
  
    total_payments = process_payments(items)
    print(f"Total: {total_payments:.2f}")

if __name__ == "__main__":
    run_batch()