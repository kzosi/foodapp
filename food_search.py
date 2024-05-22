import requests
import sqlite3
import os
import json
from translate import Translator

API_KEY = 'aa5e91a3425e4a82aae2a4efaf3f3964'
BASE_URL = 'https://api.spoonacular.com/recipes/complexSearch'
DETAILS_URL = 'https://api.spoonacular.com/recipes/{id}/information?includeNutrition=true'
NUTRITION_URL = 'https://api.spoonacular.com/recipes/{id}/nutritionWidget.json'

translator = Translator(to_lang="pl")

def translate_to_polish(text):
    try:
        return translator.translate(text)
    except Exception as e:
        print(f"Error translating '{text}': {e}")
        return text

def get_normalized_filename(ingredients):
    normalized = '_'.join(sorted([ingredient.lower().replace(' ', '').replace('-', '') for ingredient in ingredients]))
    return f"{normalized}.html"

def fetch_meals_from_api(included_ingredients, excluded_ingredients):
    params = {
        'includeIngredients': ','.join(included_ingredients),
        'excludeIngredients': ','.join(excluded_ingredients),
        'number': 5,
        'apiKey': API_KEY
    }
    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        return response.json().get('results', [])
    except requests.RequestException as e:
        print(f"Error fetching meals from API: {e}")
        return []

def fetch_meal_details(meal_id):
    url = DETAILS_URL.format(id=meal_id)
    params = {'apiKey': API_KEY}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching meal details for ID {meal_id}: {e}")
        return {}

def fetch_nutrition_details(meal_id):
    url = NUTRITION_URL.format(id=meal_id)
    params = {'apiKey': API_KEY}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching nutrition details for ID {meal_id}: {e}")
        return {}

def save_meal_to_db(included_ingredients, excluded_ingredients, meal_data):
    try:
        conn = sqlite3.connect('meals.db')
        c = conn.cursor()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()

def get_meals_from_db(included_ingredients, excluded_ingredients):
    try:
        conn = sqlite3.connect('meals.db')
        c = conn.cursor()
        c.execute('''
            SELECT meal_data FROM meals WHERE included_ingredients=? AND excluded_ingredients=?
        ''', (json.dumps(included_ingredients), json.dumps(excluded_ingredients)))
        row = c.fetchone()
        if row:
            return json.loads(row[0])
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()
    return None

def normalize_ingredient_name(name):
    return name.lower().replace(' ', '').replace('-', '')

def generate_html(meals, filename):
    try:
        html_content = '<html><head><title>Meal Suggestions</title><meta charset="UTF-8"></head><body>'
        for meal in meals:
            html_content += f"<h2>{meal['title']}</h2>"
            html_content += f"<img src='{meal['image']}' alt='{meal['title']}'><br>" if 'image' in meal else ""
            html_content += f"<strong>Ingredients already present:</strong> {', '.join(meal['ingredients_present'])}<br>"
            html_content += f"<strong>Missing ingredients:</strong> {', '.join(meal['missing_ingredients'])}<br>"
            html_content += f"<strong>Carbs:</strong> {meal['nutrition']['carbs']}<br>"
            html_content += f"<strong>Proteins:</strong> {meal['nutrition']['proteins']}<br>"
            html_content += f"<strong>Calories:</strong> {meal['nutrition']['calories']}<br>"
            html_content += "<hr>"
        html_content += '</body></html>'
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
    except IOError as e:
        print(f"Error writing to HTML file {filename}: {e}")

def find_food(included_ingredients, excluded_ingredients):
    intersection = set(included_ingredients) & set(excluded_ingredients)
    if intersection:
        print("Error: The following ingredients are both included and excluded:", ', '.join(intersection))
        return

    meals = get_meals_from_db(included_ingredients, excluded_ingredients)
    if not meals:
        api_meals = fetch_meals_from_api(included_ingredients, excluded_ingredients)
        meals = []
        for api_meal in api_meals:
            details = fetch_meal_details(api_meal['id'])
            if not details or 'image' not in details:
                continue
            ingredients_present = [ingredient for ingredient in included_ingredients if ingredient in [ing['name'] for ing in details.get('extendedIngredients', [])]]
            missing_ingredients = [ingredient['name'] for ingredient in details.get('extendedIngredients', []) if ingredient['name'] not in included_ingredients]
            missing_ingredients_translated = [f"{translate_to_polish(ingredient)} ({ingredient})" for ingredient in missing_ingredients]

            nutrition = {
                'carbs': 'N/A',
                'proteins': 'N/A',
                'calories': 'N/A'
            }
            if 'nutrition' in details:
                nutrients = {n['name'].lower(): n['amount'] for n in details['nutrition']['nutrients']}
                nutrition['carbs'] = nutrients.get('carbohydrates', 'N/A')
                nutrition['proteins'] = nutrients.get('protein', 'N/A')
                nutrition['calories'] = nutrients.get('calories', 'N/A')

            meals.append({
                'title': details['title'],
                'image': details['image'],
                'ingredients_present': sorted(ingredients_present),
                'missing_ingredients': sorted(missing_ingredients_translated),
                'nutrition': nutrition
            })
        save_meal_to_db(included_ingredients, excluded_ingredients, meals)
    
    filename = get_normalized_filename(included_ingredients)
    generate_html(meals, filename)
    

if __name__ == "__main__":
    included = ['ham', 'chicken', 'onion']
    excluded = ['potato']
    find_food(included, excluded)