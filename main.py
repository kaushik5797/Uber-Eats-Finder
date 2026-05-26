from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
import requests
import urllib.parse
import json

app = FastAPI(title="Protein Eats Finder API")

# ---------------------------------------------------------
# THE LOGIC ENGINE (Ready and waiting for the new data structure)
# ---------------------------------------------------------
def process_uber_eats_data(raw_restaurant_data, protein_choice):
    approved_meals = []
    forbidden_words = ['pork', 'bacon', 'sausage', 'ham', 'pepperoni']

    for item in raw_restaurant_data:
        if item.get('restaurant_rating', 0) < 4.0 or item.get('restaurant_reviews', 0) < 50:
            continue
            
        item_name_lower = item.get('item_name', '').lower()
        if any(bad_word in item_name_lower for bad_word in forbidden_words):
            continue
            
        total_price = item.get('item_price', 0) + item.get('delivery_fee', 0) + item.get('service_fee', 0)
        
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

        if estimated_protein == 0:
            estimated_protein = 45

        is_ratio_approved = False
        if 8.00 <= total_price <= 20.00 and 40 <= estimated_protein <= 70:
            is_ratio_approved = True
        elif 18.00 <= total_price <= 35.00 and 120 <= estimated_protein <= 140:
            is_ratio_approved = True
            
        if not is_ratio_approved:
            continue
            
        deep_link = f"https://www.ubereats.com/gb/store/{item.get('store_slug', 'restaurant')}/{item.get('store_uuid', '123')}?pl={item.get('item_uuid', '456')}"
        
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
# THE LIVE RAPID-API CONNECTION (NEW API - DIAGNOSTIC MODE)
# ---------------------------------------------------------
@app.get("/api/hungry")
def get_hungry_meals(postcode: str = "NW4 2RR", protein: str = "chicken"):
    
    # New endpoint from your screenshot
    url = "https://uber-eats5.p.rapidapi.com/getSearchSuggestions"
    
    # Passing the protein choice directly to the userQuery parameter
    querystring = {"userQuery": protein}
    
    # New Host and API Key from your screenshot
    headers = {
        "x-rapidapi-key": "5ceb67f994mshe7a8f56e18d1245p1fea92jsn074961c958f9",
        "x-rapidapi-host": "uber-eats5.p.rapidapi.com"
    }
    
    try:
        response = requests.get(url, headers=headers, params=querystring)
        live_api_data = response.json()
        
        # We are bypassing the translation layer and math engine entirely 
        # and returning the raw JSON from this new API so we can map its structure.
        return PlainTextResponse(content=json.dumps(live_api_data))
        
    except Exception as e:
        error_msg = {"status": "error", "message": f"Failed to connect to the new API: {str(e)}"}
        return PlainTextResponse(content=json.dumps(error_msg))
