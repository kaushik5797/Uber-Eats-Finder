from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Protein Eats Finder API")

# The math and logic engine
def process_uber_eats_data(raw_restaurant_data):
    approved_meals = []
    forbidden_words = ['pork', 'beef', 'bacon', 'sausage', 'ham', 'steak', 'pepperoni']

    for item in raw_restaurant_data:
        # Rule 1: Quality Check
        if item['restaurant_rating'] < 4.3 or item['restaurant_reviews'] < 500:
            continue
            
        # Rule 2: Dietary Check
        item_name_lower = item['item_name'].lower()
        if any(bad_word in item_name_lower for bad_word in forbidden_words):
            continue
            
        # Rule 3: Financial Math
        total_price = item['item_price'] + item['delivery_fee'] + item['service_fee']
        
        # Rule 4: Protein Heuristic
        estimated_protein = 0
        if any(keyword in item_name_lower for keyword in ["double chicken", "half chicken", "platter"]):
            estimated_protein = 130  
        elif any(keyword in item_name_lower for keyword in ["chicken breast", "shish", "salmon"]):
            estimated_protein = 55
            
        # Ratio Rule Application
        is_ratio_approved = False
        if 10.00 <= total_price <= 14.00 and 50 <= estimated_protein <= 60:
            is_ratio_approved = True
        elif 18.00 <= total_price <= 22.00 and 120 <= estimated_protein <= 140:
            is_ratio_approved = True
            
        if not is_ratio_approved:
            continue
            
        # Rule 5: Deep Link
        deep_link = f"https://www.ubereats.com/store/{item['store_slug']}/{item['store_uuid']}?pl={item['item_uuid']}"
        
        approved_meals.append({
            "name": item['item_name'],
            "restaurant": item['restaurant_name'],
            "all_in_price": round(total_price, 2),
            "estimated_protein": f"~{estimated_protein}g",
            "rating": item['restaurant_rating'],
            "reviews": item['restaurant_reviews'],
            "order_link": deep_link
        })
        
    return approved_meals


# The API Endpoint that ChatGPT/Claude will call
@app.get("/api/hungry")
def get_hungry_meals():
    # Mock data simulating a raw payload from an Uber Eats API
    mock_live_data = [
        {
            "restaurant_name": "Chick Inn Village",
            "restaurant_rating": 4.8,
            "restaurant_reviews": 6500,
            "item_name": "Grilled Peri Peri Chicken - Full Platter",
            "item_price": 16.00,
            "delivery_fee": 1.99,
            "service_fee": 1.92,
            "store_slug": "chick-inn-village",
            "store_uuid": "12345",
            "item_uuid": "abcde"
        },
        {
            "restaurant_name": "Mangal Express",
            "restaurant_rating": 4.5,
            "restaurant_reviews": 850,
            "item_name": "Chicken Shish Wrap",
            "item_price": 8.50,
            "delivery_fee": 2.00,
            "service_fee": 1.30,
            "store_slug": "mangal-express",
            "store_uuid": "67890",
            "item_uuid": "vwxyz"
        },
        {
            "restaurant_name": "Bacon Burger Joint", # Will be filtered out by dietary rule
            "restaurant_rating": 4.9,
            "restaurant_reviews": 1000,
            "item_name": "Double Bacon Cheese Burger",
            "item_price": 10.00,
            "delivery_fee": 1.00,
            "service_fee": 1.00,
            "store_slug": "bacon-joint",
            "store_uuid": "11111",
            "item_uuid": "22222"
        }
    ]
    
    # Process the data through your logic engine
    final_meals = process_uber_eats_data(mock_live_data)
    
    # Return the clean JSON to the LLM
    return {"status": "success", "results": final_meals}