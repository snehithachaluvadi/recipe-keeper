import json
import os
import hashlib
from datetime import datetime
from PIL import Image
import pandas as pd
from collections import Counter

# --- PATH DEFINITIONS ---
DATA_DIR = "data"
RECIPE_FILE = os.path.join(DATA_DIR, "recipes.json")
USERS_FILE = os.path.join(DATA_DIR, "users.json")
UPLOADS_DIR = os.path.join(DATA_DIR, "uploads")

# --- DIRECTORY SETUP ---
os.makedirs(UPLOADS_DIR, exist_ok=True)

# --- USER MANAGEMENT FUNCTIONS ---

def hash_password(password):
    """Hashes the password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    """Loads all users from the users JSON file."""
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_user(username, password):
    """Saves a new user with a hashed password."""
    users = load_users()
    # Check if user already exists
    if any(user['username'] == username for user in users):
        return False
    
    new_user = {"username": username, "password_hash": hash_password(password)}
    users.append(new_user)
    
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)
    return True

def verify_user(username, password):
    """Verifies user credentials against the stored hash."""
    users = load_users()
    hashed_password = hash_password(password)
    for user in users:
        if user['username'] == username and user['password_hash'] == hashed_password:
            return True
    return False

# --- RECIPE MANAGEMENT FUNCTIONS ---

def save_uploaded_image(uploaded_file):
    """Saves and optimizes an uploaded image, returning its path."""
    if uploaded_file is None:
        return None
    try:
        img = Image.open(uploaded_file)
        img.thumbnail((800, 800)) # Resize for optimization
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{uploaded_file.name}"
        filepath = os.path.join(UPLOADS_DIR, filename)
        
        img.save(filepath, optimize=True, quality=85)
        return filepath
    except Exception as e:
        print(f"Error saving image: {e}")
        return None

def load_recipes():
    """Loads all recipes from the JSON file."""
    if not os.path.exists(RECIPE_FILE):
        return []
    with open(RECIPE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_recipe(recipe_data):
    """Saves a new recipe to the JSON file."""
    recipes = load_recipes()
    recipes.append(recipe_data)
    with open(RECIPE_FILE, "w", encoding="utf-8") as f:
        json.dump(recipes, f, indent=4, ensure_ascii=False)

# --- DASHBOARD/ANALYTICS FUNCTIONS ---

def get_ingredient_usage_graph():
    """Analyzes all recipes and returns a DataFrame for a bar chart."""
    recipes = load_recipes()
    if not recipes:
        return None

    all_ingredients = []
    for recipe in recipes:
        # The new structure is a list of dicts
        if isinstance(recipe.get('ingredients'), list):
            for item in recipe['ingredients']:
                # Normalize the ingredient name to lowercase for accurate counting
                all_ingredients.append(item['name'].strip().lower())

    if not all_ingredients:
        return None

    ingredient_counts = Counter(all_ingredients)
    
    # Convert to a pandas DataFrame for Streamlit charts
    df = pd.DataFrame(ingredient_counts.items(), columns=['Ingredient', 'Count'])
    df = df.sort_values('Count', ascending=False).head(15) # Show top 15
    df.set_index('Ingredient', inplace=True)
    
    return df