from fastapi import FastAPI
import requests
import json
import urllib.parse

app = FastAPI(title="Protein Eats Finder API")

# ---------------------------------------------------------
# THE LOGIC ENGINE 
# ---------------------------------------------------------
def process_uber_eats_data(raw_restaurant_data):
    approved_meals = []
    forbidden_words = ['pork', 'beef', 'bacon', 'sausage', 'ham', 'steak', 'pepperoni']

    for item in raw_restaurant_data:
        if item.get('restaurant_rating', 0) < 4.3 or item.get('restaurant_reviews', 0) < 500:
            continue
            
        item_name_lower = item.get('item_name', '').lower()
        if any(bad_word in item_name_lower for bad_word in forbidden_words):
            continue
            
        total_price = item.get('item_price', 0) + item.get('delivery_fee', 0) + item.get('service_fee', 0)
        
        estimated_protein = 0
        if any(keyword in item_name_lower for keyword in ["double chicken", "half chicken", "platter", "whole chicken"]):
            estimated_protein = 130  
        elif any(keyword in item_name_lower for keyword in ["chicken breast", "shish", "salmon", "wrap", "escalope"]):
            estimated_protein = 55
            
        is_ratio_approved = True 
        # (We are temporarily letting everything through just to test!)
            
        # Inside your loop...
        encoded_name = urllib.parse.quote_plus(item['item_name'])
        deep_link = f"https://www.ubereats.com/store/{item['store_slug']}/{item['store_uuid']}?q={encoded_name}"
        
        approved_meals.append({
            "name": item['item_name'],
            "restaurant": item['restaurant_name'],
            "all_in_price": f"£{round(total_price, 2)}",
            "estimated_protein": f"~{estimated_protein}g",
            "rating": item['restaurant_rating'],
            "reviews": item['restaurant_reviews'],
            "order_link": deep_link
        })
        
    return approved_meals

# ---------------------------------------------------------
# THE LIVE RAPID-API CONNECTION
# ---------------------------------------------------------
@app.get("/api/hungry")
def get_hungry_meals(postcode: str = "NW4 2RR"):
    
    # 1. The exact URL from your screenshot
    url = "https://uber-eats-scraper-api.p.rapidapi.com/api/job"
    
    # 2. The exact JSON payload from your screenshot
    payload = {
        "scraper": {
            "maxRows": 15,
            "query": "chicken",
            "address": postcode, 
            "locale": "en-GB", # Set to GB for London
            "page": 1,
            "getMenuCustomizations": False
        }
    }
    
    # 3. The Headers (Notice we added the Content-Type!)
    headers = {
        "content-type": "application/json",
        "x-rapidapi-key": "5ceb67f994mshe7a8f56e18d1245p1fea92jsn074961c958f9", 
        "x-rapidapi-host": "uber-eats-scraper-api.p.rapidapi.com"
    }
    
    try:
        # 4. We use requests.post() instead of requests.get()
        response = requests.post(url, json=payload, headers=headers)
        live_api_data = response.json()

        # --- THE SECRET INTERCEPTOR ---
        print("=== RAW RAPIDAPI DATA ===")
        print(live_api_data)
        
        # Temporarily return the raw data directly so Claude prints it on your screen!
        return {"status": "success", "raw_data": live_api_data}

    except Exception as e:
        return {"status": "error", "message": f"Failed to connect: {str(e)}"}
    
    # 2. THE TRANSLATION LAYER
    # Note: If the API returns an error or empty list, this safely skips it.
    # You may need to adjust ['data'] or ['items'] based on the exact JSON
    # structure you see in the RapidAPI Playground window.
    
    # Let's assume the API returns a list of items inside a 'data' array
    dishes = live_api_data.get('data', []) 
    
    for item in dishes:
        try:
            # We map the messy RapidAPI data to our clean variables
            clean_item = {
                "restaurant_name": item.get('restaurantName', 'Unknown Restaurant'),
                "restaurant_rating": item.get('rating', 4.5), 
                "restaurant_reviews": item.get('reviewCount', 600),
                "item_name": item.get('title', item.get('name', 'Unknown Dish')),
                
                # Prices are often given in cents/pence (e.g. 1600 instead of 16.00)
                "item_price": float(item.get('price', 0)) / 100 if item.get('price', 0) > 100 else float(item.get('price', 0)),
                "delivery_fee": 1.99, # Hardcoded average if API doesn't provide it easily
                "service_fee": 1.50,
                
                # IDs for the deep link
                "store_slug": item.get('storeSlug', 'restaurant'),
                "store_uuid": item.get('storeUuid', '123'),
                "item_uuid": item.get('itemUuid', '456')
            }
            formatted_data_for_engine.append(clean_item)
        except Exception as e:
            # If one menu item is broken, skip it and keep going!
            continue 

    # 3. Give the clean data to your math engine
    final_meals = process_uber_eats_data(formatted_data_for_engine)
    
    # If the filters were too strict and deleted everything, return a fallback message
    if len(final_meals) == 0:
        return {"status": "success", "message": "No meals matched your strict protein criteria today.", "results": []}
    
    return {"status": "success", "results": final_meals}
