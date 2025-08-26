import streamlit as st
import pandas as pd
from datetime import datetime
from utils.db_utils import (
    save_recipe, load_recipes, save_uploaded_image,
    verify_user, save_user, get_ingredient_usage_graph
)

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Recipe Keeper",
    page_icon="🍲",
    layout="wide"
)

# --- AUTHENTICATION LOGIC ---

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
if 'page' not in st.session_state:
    st.session_state['page'] = 'login'
if 'ingredients' not in st.session_state:
    st.session_state['ingredients'] = []


def login_page():
    st.header("Login")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        if submitted:
            if verify_user(username, password):
                st.session_state['authenticated'] = True
                st.session_state['username'] = username
                st.rerun() # Rerun the script to show the main app
            else:
                st.error("Invalid username or password")
    
    if st.button("Don't have an account? Sign Up"):
        st.session_state['page'] = 'signup'
        st.rerun()


def signup_page():
    st.header("Sign Up")
    with st.form("signup_form"):
        username = st.text_input("Choose a Username")
        password = st.text_input("Choose a Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        submitted = st.form_submit_button("Sign Up")
        if submitted:
            if not username or not password:
                st.error("Username and password cannot be empty.")
            elif password != confirm_password:
                st.error("Passwords do not match.")
            elif save_user(username, password):
                st.success("Account created successfully! Please log in.")
                st.session_state['page'] = 'login'
                st.rerun()
            else:
                st.error("Username already exists.")

    if st.button("Already have an account? Login"):
        st.session_state['page'] = 'login'
        st.rerun()


# --- MAIN APPLICATION ---

def main_app():
    st.sidebar.title(f"Welcome, {st.session_state['username']}! 👋")
    st.sidebar.markdown("---")
    if st.sidebar.button("Logout"):
        st.session_state['authenticated'] = False
        st.session_state['page'] = 'login'
        st.session_state.pop('username', None) # Clear username
        st.session_state['ingredients'] = [] # Clear ingredients list
        st.rerun()

    st.title("🍲 Recipe Keeper")
    st.markdown("Your digital space for family culinary traditions.")

    tab1, tab2, tab3 = st.tabs(["🍳 Submit Recipe*", "📖 Community Cookbook", "📊 Dashboard*"])

    # --- TAB 1: SUBMIT RECIPE ---
    with tab1:
        st.header("Add a New Recipe")
        with st.form(key="recipe_form", clear_on_submit=True):
            dish_name = st.text_input("Dish Name*")
            uploaded_photo = st.file_uploader("Upload a Photo", type=["jpg", "png", "jpeg"])
            instructions = st.text_area("Instructions*")
            
            st.markdown("---")
            st.subheader("Add Ingredients")

            # Ingredient input fields
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            with col1:
                ing_name = st.text_input("Ingredient Name", key="ing_name")
            with col2:
                ing_qty = st.text_input("Quantity", key="ing_qty")
            with col3:
                ing_unit = st.selectbox("Unit", ["", "g", "kg", "ml", "l", "tsp", "tbsp", "cup", "pcs"], key="ing_unit")
            with col4:
                # Use a button to add to the session state list
                add_ingredient = st.form_submit_button("Add")

            # Logic to add ingredient to the list in session state
            if add_ingredient and ing_name:
                st.session_state.ingredients.append({"name": ing_name, "quantity": ing_qty, "unit": ing_unit})
            
            # Display current ingredients
            if st.session_state.ingredients:
                st.write("Current Ingredients:")
                current_ingredients_df = pd.DataFrame(st.session_state.ingredients)
                st.dataframe(current_ingredients_df, use_container_width=True)

            st.markdown("---")
            final_submit_button = st.form_submit_button(label="✅ Submit Full Recipe")

            if final_submit_button:
                if not dish_name or not instructions or not st.session_state.ingredients:
                    st.warning("Please fill in Dish Name, Instructions, and add at least one ingredient.")
                else:
                    image_path = save_uploaded_image(uploaded_photo)
                    recipe_data = {
                        "id": datetime.now().isoformat(),
                        "submitted_by": st.session_state['username'],
                        "dish_name": dish_name,
                        "ingredients": st.session_state.ingredients,
                        "instructions": instructions,
                        "image_path": image_path,
                    }
                    save_recipe(recipe_data)
                    st.success(f"Recipe '{dish_name}' submitted!")
                    st.session_state.ingredients = [] # Clear for next recipe

    # --- TAB 2: COMMUNITY COOKBOOK ---
    with tab2:
        st.header("Search and Explore Recipes")
        search_query = st.text_input("Search by dish name or ingredient", "")
        
        all_recipes = load_recipes()
        
        # Filtering logic
        filtered_recipes = []
        if search_query:
            query = search_query.lower()
            for recipe in all_recipes:
                # Check dish name
                if query in recipe['dish_name'].lower():
                    filtered_recipes.append(recipe)
                    continue
                # Check ingredients
                ing_match = any(query in item['name'].lower() for item in recipe.get('ingredients', []))
                if ing_match:
                    filtered_recipes.append(recipe)
        else:
            filtered_recipes = all_recipes
            
        if not filtered_recipes:
            st.info("No recipes found. Try a different search or add a new recipe!")
        else:
            for recipe in reversed(filtered_recipes):
                with st.expander(f"{recipe['dish_name']}** (by {recipe['submitted_by']})"):
                    left, right = st.columns([1, 2])
                    with left:
                        if recipe.get("image_path"):
                            st.image(recipe["image_path"])
                        else:
                            st.image("https://placehold.co/400x300?text=No+Image")
                    with right:
                        st.subheader("🌿 Ingredients")
                        ing_df = pd.DataFrame(recipe.get('ingredients', []))
                        st.dataframe(ing_df, hide_index=True)
                    
                    st.subheader("📖 Instructions")
                    st.markdown(recipe["instructions"])

    # --- TAB 3: DASHBOARD ---
    with tab3:
        st.header("Recipe Dashboard")
        st.markdown("Here are some analytics on the community's recipes.")
        
        ingredient_usage = get_ingredient_usage_graph()
        
        if ingredient_usage is not None:
            st.subheader("Most Popular Ingredients")
            st.bar_chart(ingredient_usage)
        else:
            st.info("Not enough data to display a graph. Add more recipes!")

# --- ROUTING LOGIC ---
if not st.session_state['authenticated']:
    st.warning("🔒 This is a demo application. Do not use real passwords.")
    if st.session_state['page'] == 'login':
        login_page()
    elif st.session_state['page'] == 'signup':
        signup_page()
else:
    main_app()