from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
import requests
import urllib.parse
import json

app = FastAPI(title="Protein Eats Finder API")

# ---------------------------------------------------------
# THE LOGIC ENGINE 
# ---------------------------------------------------------
def process_uber_eats_data(raw_restaurant_data, protein_choice):
    approved_meals = []
    forbidden_words = ['pork', 'bacon', 'sausage', 'ham', 'pepperoni']

    for item in raw_restaurant_data:
        if item.get('restaurant_rating', 0) < 4.3 or item.get('restaurant_reviews', 0) < 500:
            continue
            
        item_name_lower = item.get('item_name', '').lower()
        if any(bad_word in item_name_lower for bad_word in forbidden_words):
            continue
            
        total_price = item.get('item_price', 0) + item.get('delivery_fee', 0) + item.get('service_fee', 0)
        
        estimated_protein = 0
        if protein_choice == "chicken":
            if any(keyword in item_name_lower for keyword in ["double chicken", "half chicken", "platter", "whole"]):
                estimated_protein = 130  
            elif any(keyword in item_name_lower for keyword in ["breast", "shish", "wrap", "escalope"]):
                estimated_protein = 55
        elif protein_choice == "fish":
            if any(keyword in item_name_lower for keyword in ["salmon", "seabass", "mixed grill"]):
                estimated_protein = 55
            elif any(keyword in item_name_lower for keyword in ["tuna", "cod", "fillet"]):
                estimated_protein = 40
        elif protein_choice in ["lamb", "mutton"]:
            if any(keyword in item_name_lower for keyword in ["chops", "shank", "platter", "mixed grill"]):
                estimated_protein = 130
            elif any(keyword in item_name_lower for keyword in ["kebab", "shish", "rogan josh", "tikka", "curry"]):
                estimated_protein = 55

        is_ratio_approved = False
        if 8.00 <= total_price <= 12.00 and 40 <= estimated_protein <= 60:
            is_ratio_approved = True
        elif 16.00 <= total_price <= 22.00 and 120 <= estimated_protein <= 140:
            is_ratio_approved = True
            
        if not is_ratio_approved:
            continue
            
        encoded_name = urllib.parse.quote_plus(item['item_name'])
        deep_link = f"https://www.ubereats.com/store/{item['store_slug']}/{item['store_uuid']}?pl={item.get('item_uuid', '456')}"
        
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
def get_hungry_meals(postcode: str = "NW4 2RR", protein: str = "chicken"):
    
    url = "https://uber-eats-scraper-api.p.rapidapi.com/api/job"
    
    payload = {
        "scraper": {
            "maxRows": 25, 
            "query": protein, 
            "address": postcode, 
            "locale": "en-GB", 
            "page": 1,
            "getMenuCustomizations": False
        }
    }
    
    headers = {
        "content-type": "application/json",
        "x-rapidapi-key": "PASTE_YOUR_KEY_HERE", # <--- DON'T FORGET THIS!
        "x-rapidapi-host": "uber-eats-scraper-api.p.rapidapi.com"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        live_api_data = response.json()
    except Exception as e:
        error_msg = {"status": "error", "message": "Failed to connect to RapidAPI."}
        return PlainTextResponse(content=json.dumps(error_msg))
    
    formatted_data_for_engine = []
    dishes = live_api_data.get('data', []) 
    
    for item in dishes:
        try:
            clean_item = {
                "restaurant_name": item.get('restaurantName', 'Unknown Restaurant'),
                "restaurant_rating": item.get('rating', 4.5), 
                "restaurant_reviews": item.get('reviewCount', 600),
                "item_name": item.get('title', item.get('name', 'Unknown Dish')),
                "item_price": float(item.get('price', 0)) / 100 if item.get('price', 0) > 100 else float(item.get('price', 0)),
                "delivery_fee": 1.99, 
                "service_fee": 1.50,
                "store_slug": item.get('storeSlug', 'restaurant'),
                "store_uuid": item.get('storeUuid', '123'),
                "item_uuid": item.get('itemUuid', item.get('id', '456')) # Added a fallback check for 'id'
            }
            formatted_data_for_engine.append(clean_item)
        except Exception as e:
            continue 

    final_meals = process_uber_eats_data(formatted_data_for_engine, protein.lower())
    
    # --- THE DISGUISE ---
    # We take the final dictionary, convert it to a string using json.dumps(), 
    # and send it as a PlainTextResponse so the Claude fetch tool doesn't crash!
    
    if len(final_meals) == 0:
        fallback = {"status": "success", "message": f"No {protein} meals matched your strict protein criteria today.", "results": []}
        return PlainTextResponse(content=json.dumps(fallback))
    
    success_data = {"status": "success", "results": final_meals}
    return PlainTextResponse(content=json.dumps(success_data))
