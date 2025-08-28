import streamlit as st
import pandas as pd
from datetime import datetime
import os
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

# --- AUTHENTICATION & SESSION STATE ---
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
if 'page' not in st.session_state:
    st.session_state['page'] = 'login'
if 'ingredients' not in st.session_state:
    st.session_state['ingredients'] = []
if 'dish_name' not in st.session_state:
    st.session_state['dish_name'] = ""
if 'instructions' not in st.session_state:
    st.session_state['instructions'] = ""
if 'photo_uploader' not in st.session_state:
    st.session_state['photo_uploader'] = None


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
                st.rerun()
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
        for key in st.session_state.keys():
            del st.session_state[key]
        st.rerun()

    st.title("🍲 Recipe Keeper")
    st.markdown("Your digital space for family culinary traditions.")

    tab1, tab2, tab3 = st.tabs(["**🍳 Submit Recipe**", "**📖 Community Cookbook**", "**📊 Dashboard**"])

    # --- TAB 1: SUBMIT RECIPE (Using a Callback to fix the error) ---
    with tab1:
        # Define the callback function that will handle the submission logic
        def submit_recipe_callback():
            # 1. Validate the inputs
            if not st.session_state.dish_name or not st.session_state.instructions or not st.session_state.ingredients:
                st.warning("Please fill in Dish Name, Instructions, and add at least one ingredient.")
                return  # Stop if validation fails
            
            # 2. Process and save the data
            image_path = save_uploaded_image(st.session_state.photo_uploader)
            recipe_data = {
                "id": datetime.now().isoformat(),
                "submitted_by": st.session_state.username,
                "dish_name": st.session_state.dish_name,
                "ingredients": st.session_state.ingredients,
                "instructions": st.session_state.instructions,
                "image_path": image_path,
            }
            save_recipe(recipe_data)
            st.success(f"Recipe '{st.session_state.dish_name}' submitted!")

            # 3. Safely clear the form fields for the next entry
            st.session_state.dish_name = ""
            st.session_state.instructions = ""
            st.session_state.ingredients = []
            st.session_state.photo_uploader = None

        st.markdown("""
        <style>
        .stButton > button {
            width: 100%; border-radius: 10px; border: 1px solid rgba(49, 51, 63, 0.2);
            background-color: #FFFFFF; color: #31333F; transition: all 0.2s ease-in-out;
        }
        .stButton > button:hover { border-color: #FF4B4B; color: #FF4B4B; }
        .stButton > button:focus { border-color: #FF4B4B; color: #FF4B4B; box-shadow: none; }
        </style>
        """, unsafe_allow_html=True)
        
        st.header("Add a New Recipe")
        
        st.text_input("Dish Name*", key="dish_name")
        st.file_uploader("Upload a Photo", type=["jpg", "png", "jpeg"], key="photo_uploader")
        st.text_area("Instructions*", key="instructions", height=200)

        st.markdown("---")
        
        st.subheader("Add Ingredients")
        
        col1, col2, col3 = st.columns([2.5, 1.5, 1])
        ing_name = col1.text_input("Ingredient Name", placeholder="Ingredient Name", label_visibility="collapsed")
        ing_qty = col2.text_input("Quantity", placeholder="Quantity", label_visibility="collapsed")
        ing_unit = col3.selectbox("Unit", ["", "g", "kg", "ml", "l", "tsp", "tbsp", "cup", "pcs"], label_visibility="collapsed")
        
        col_add, col_remove = st.columns(2)
        if col_add.button("Add Ingredient"):
            if ing_name:
                st.session_state.ingredients.append({"name": ing_name, "quantity": ing_qty, "unit": ing_unit})
                st.rerun()
            else:
                st.warning("Ingredient name cannot be empty.")
        
        if col_remove.button("Remove Last Ingredient"):
            if st.session_state.ingredients:
                st.session_state.ingredients.pop()
                st.rerun()

        if st.session_state.ingredients:
            st.write("Current Ingredients:")
            st.dataframe(pd.DataFrame(st.session_state.ingredients), use_container_width=True)

        st.markdown("---")

        # The final submit button now uses the on_click callback to prevent the error
        st.button("✅ Submit Full Recipe", on_click=submit_recipe_callback)

    # --- TAB 2: COMMUNITY COOKBOOK ---
    with tab2:
        st.header("Search and Explore Recipes")
        search_query = st.text_input("Search by dish name or ingredient", "")
        
        all_recipes = load_recipes()
        
        filtered_recipes = []
        if search_query:
            query = search_query.lower()
            for recipe in all_recipes:
                if query in recipe['dish_name'].lower() or \
                   any(query in item['name'].lower() for item in recipe.get('ingredients', [])):
                    filtered_recipes.append(recipe)
        else:
            filtered_recipes = all_recipes
            
        if not filtered_recipes:
            st.info("No recipes found. Try a different search or add a new recipe!")
        else:
            for recipe in reversed(filtered_recipes):
                with st.expander(f"**{recipe['dish_name']}** (by *{recipe['submitted_by']}*)"):
                    left, right = st.columns([1, 2])
                    with left:
                        image_path = recipe.get("image_path")
                        if image_path and os.path.exists(image_path):
                            st.image(image_path)
                        else:
                            st.image("https://placehold.co/400x300?text=No+Image")
                    with right:
                        st.subheader("🌿 Ingredients")
                        st.dataframe(pd.DataFrame(recipe.get('ingredients', [])), hide_index=True)
                    
                    st.subheader("📖 Instructions")
                    st.markdown(recipe["instructions"])

    # --- TAB 3: DASHBOARD ---
    with tab3:
        st.header("Recipe Dashboard")
        st.markdown("Here are some analytics on the community's recipes.")
        
        ingredient_usage = get_ingredient_usage_graph()
        
        if ingredient_usage is not None and not ingredient_usage.empty:
            st.subheader("Most Popular Ingredients")
            st.bar_chart(ingredient_usage)
        else:
            st.info("Not enough data to display a graph. Add more recipes!")

# --- ROUTING LOGIC ---
if not st.session_state.get('authenticated', False):
    st.warning("🔒 This is a demo application. Do not use real passwords.")
    page = st.session_state.get('page', 'login')
    if page == 'login':
        login_page()
    elif page == 'signup':
        signup_page()
else:
    main_app()