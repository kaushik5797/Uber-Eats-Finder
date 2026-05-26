from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
import requests
import urllib.parse
import json

app = FastAPI(title="Protein Eats Finder API")

# ---------------------------------------------------------
# THE LOGIC ENGINE (ALL FILTERS DISABLED)
# ---------------------------------------------------------
def process_uber_eats_data(raw_restaurant_data, protein_choice):
    approved_meals = []
    # forbidden_words = ['pork', 'bacon', 'sausage', 'ham', 'pepperoni']

    for item in raw_restaurant_data:
        
        # --- 1. QUALITY FILTER BYPASSED ---
        # if item.get('restaurant_rating', 0) < 4.0 or item.get('restaurant_reviews', 0) < 50:
        #     continue
            
        item_name_lower = item.get('item_name', '').lower()
        
        # --- 2. DIETARY FILTER BYPASSED ---
        # if any(bad_word in item_name_lower for bad_word in forbidden_words):
        #     continue
            
        total_price = item.get('item_price', 0) + item.get('delivery_fee', 0) + item.get('service_fee', 0)
        
        # --- DYNAMIC PROTEIN HEURISTICS (Still active so your UI looks good) ---
        estimated_protein = 0
        if protein_choice == "chicken":
            if any(keyword in item_name_lower for keyword in ["double", "half", "platter", "whole"]):
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

        # Safety Net (Defaults to 45g if no keywords match)
        if estimated_protein == 0:
            estimated_protein = 45

        # --- 3. THE BOUNCER BYPASSED ---
        # We automatically approve every single meal, regardless of price!
        is_ratio_approved = True
            
        if not is_ratio_approved:
            continue
            
        deep_link = f"https://www.ubereats.com/store/{item['store_slug']}/{item['store_uuid']}?pl={item.get('item_uuid', '456')}"
        
        approved_meals.append({
            "name": item['item_name'],
            "restaurant": item['restaurant_name'],
            "all_in_price": f"£{round(total_price, 2)}",
            "estimated_protein": f"~{estimated_protein}g",
            "rating": item.get('restaurant_rating', 'N/A'), # Added N/A fallback for missing ratings
            "reviews": item.get('restaurant_reviews', 'N/A'),
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
            "maxRows": 50, 
            "query": protein, 
            "address": postcode, 
            "locale": "en-GB", 
            "page": 1,
            "getMenuCustomizations": False
        }
    }
    
    headers = {
        "content-type": "application/json",
        "x-rapidapi-key": "5ceb67f994mshe7a8f56e18d1245p1fea92jsn074961c958f9", 
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
                "item_uuid": item.get('itemUuid', item.get('id', '456'))
            }
            formatted_data_for_engine.append(clean_item)
        except Exception as e:
            continue 

    final_meals = process_uber_eats_data(formatted_data_for_engine, protein.lower())
    
    if len(final_meals) == 0:
        fallback = {"status": "success", "message": f"No {protein} meals found on Uber Eats for this postcode right now.", "results": []}
        return PlainTextResponse(content=json.dumps(fallback))
    
    success_data = {"status": "success", "results": final_meals}
    return PlainTextResponse(content=json.dumps(success_data))
