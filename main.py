from fastapi import FastAPI
import requests # <-- The new tool we added!

app = FastAPI(title="Protein Eats Finder API")

# ---------------------------------------------------------
# THE LOGIC ENGINE (Exactly the same as before)
# ---------------------------------------------------------
def process_uber_eats_data(raw_restaurant_data):
    approved_meals = []
    forbidden_words = ['pork', 'beef', 'bacon', 'sausage', 'ham', 'steak', 'pepperoni']

    for item in raw_restaurant_data:
        if item['restaurant_rating'] < 4.3 or item['restaurant_reviews'] < 500:
            continue
            
        item_name_lower = item['item_name'].lower()
        if any(bad_word in item_name_lower for bad_word in forbidden_words):
            continue
            
        total_price = item['item_price'] + item['delivery_fee'] + item['service_fee']
        
        estimated_protein = 0
        if any(keyword in item_name_lower for keyword in ["double chicken", "half chicken", "platter"]):
            estimated_protein = 130  
        elif any(keyword in item_name_lower for keyword in ["chicken breast", "shish", "salmon", "wrap"]):
            estimated_protein = 55
            
        is_ratio_approved = False
        if 10.00 <= total_price <= 14.00 and 50 <= estimated_protein <= 60:
            is_ratio_approved = True
        elif 18.00 <= total_price <= 22.00 and 120 <= estimated_protein <= 140:
            is_ratio_approved = True
            
        if not is_ratio_approved:
            continue
            
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

# ---------------------------------------------------------
# THE NEW LIVE INTERNET CONNECTION
# ---------------------------------------------------------
@app.get("/api/hungry")
def get_hungry_meals():
    # 1. Ask RapidAPI for the data
    url = "https://uber-eats-scraper-api.p.rapidapi.com/api/job"
    
    headers = {
        "X-RapidAPI-Key": "5ceb67f994mshe7a8f56e18d1245p1fea92jsn074961c958f9",
        "X-RapidAPI-Host": "uber-eats-scraper-api.p.rapidapi.com"
    }
    
    # Send the request to the internet!
    response = requests.get(url, headers=headers)
    live_api_data = response.json()
    
    formatted_data_for_engine = []
    
    # 2. The Translation Layer
    # You will need to look at the RapidAPI response and change these 
    # to match whatever weird names the API creator used.
    # (I have used generic examples below)
    
    for item in live_api_data.get('data', []): 
        try:
            clean_item = {
                "restaurant_name": item['restaurant']['name'],
                "restaurant_rating": item['restaurant']['rating'],
                "restaurant_reviews": item['restaurant']['reviewCount'],
                "item_name": item['dish']['title'],
                "item_price": item['dish']['price'] / 100, # APIs often give prices in pennies
                "delivery_fee": 2.50, # You might have to hardcode this if the API doesn't provide it
                "service_fee": 1.50,
                "store_slug": item['restaurant']['slug'],
                "store_uuid": item['restaurant']['id'],
                "item_uuid": item['dish']['id']
            }
            formatted_data_for_engine.append(clean_item)
        except KeyError:
            # If a menu item is missing a price or a name, just skip it and don't crash
            continue 

    # 3. Give the clean data to your math engine
    final_meals = process_uber_eats_data(formatted_data_for_engine)
    
    return {"status": "success", "results": final_meals}
