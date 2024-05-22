import unittest
from unittest.mock import patch, MagicMock
import sqlite3
import json
from translate import Translator
from food_search import (
    translate_to_polish, get_normalized_filename, fetch_meals_from_api,
    fetch_meal_details, fetch_nutrition_details, save_meal_to_db,
    get_meals_from_db, normalize_ingredient_name, generate_html, find_food
)

class TestMealFunctions(unittest.TestCase):
    @patch.object(Translator, 'translate', return_value='translated_text')
    def test_translate_to_polish(self, mock_translate):
        self.assertEqual(translate_to_polish('test'), 'translated_text')
        mock_translate.assert_called_once_with('test')

    def test_get_normalized_filename(self):
        self.assertEqual(get_normalized_filename(['Feta', 'Eggplant', 'Onion']), 'eggplant_feta_onion.html')
        self.assertEqual(get_normalized_filename(['Feta-Onion', 'Eggplant']), 'eggplant_fetaonion.html')

    @patch('requests.get')
    def test_fetch_meals_from_api(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {'results': [{'id': 1, 'title': 'Test Meal'}]}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        included_ingredients = ['feta', 'eggplant']
        excluded_ingredients = ['potato']
        meals = fetch_meals_from_api(included_ingredients, excluded_ingredients)
        self.assertEqual(meals, [{'id': 1, 'title': 'Test Meal'}])
        mock_get.assert_called_once_with('https://api.spoonacular.com/recipes/complexSearch', params={
            'includeIngredients': 'feta,eggplant',
            'excludeIngredients': 'potato',
            'number': 5,
            'apiKey': 'aa5e91a3425e4a82aae2a4efaf3f3964'
        })

    @patch('requests.get')
    def test_fetch_meal_details(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {'id': 1, 'title': 'Test Meal', 'image': 'test.jpg'}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        meal_details = fetch_meal_details(1)
        self.assertEqual(meal_details, {'id': 1, 'title': 'Test Meal', 'image': 'test.jpg'})
        mock_get.assert_called_once_with('https://api.spoonacular.com/recipes/{id}/information?includeNutrition=true'.format(id=1), params={'apiKey': 'aa5e91a3425e4a82aae2a4efaf3f3964'})

    @patch('requests.get')
    def test_fetch_nutrition_details(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {'carbs': '20g', 'proteins': '10g', 'calories': '200'}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        nutrition_details = fetch_nutrition_details(1)
        self.assertEqual(nutrition_details, {'carbs': '20g', 'proteins': '10g', 'calories': '200'})
        mock_get.assert_called_once_with('https://api.spoonacular.com/recipes/{id}/nutritionWidget.json'.format(id=1), params={'apiKey': 'aa5e91a3425e4a82aae2a4efaf3f3964'})

    @patch('sqlite3.connect')
    def test_save_meal_to_db(self, mock_connect):
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        included_ingredients = ['feta', 'eggplant']
        excluded_ingredients = ['potato']
        meal_data = [{'id': 1, 'title': 'Test Meal'}]

        save_meal_to_db(included_ingredients, excluded_ingredients, meal_data)
        mock_connect.assert_called_once_with('meals.db')
        mock_conn.cursor.assert_called_once()

    @patch('sqlite3.connect')
    def test_get_meals_from_db(self, mock_connect):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = [json.dumps([{'id': 1, 'title': 'Test Meal'}])]
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        included_ingredients = ['feta', 'eggplant']
        excluded_ingredients = ['potato']
        meals = get_meals_from_db(included_ingredients, excluded_ingredients)
        self.assertEqual(meals, [{'id': 1, 'title': 'Test Meal'}])
        mock_connect.assert_called_once_with('meals.db')
        mock_conn.cursor.assert_called_once()
        mock_cursor.execute.assert_called_once_with('''
            SELECT meal_data FROM meals WHERE included_ingredients=? AND excluded_ingredients=?
        ''', (json.dumps(included_ingredients), json.dumps(excluded_ingredients)))

    def test_normalize_ingredient_name(self):
        self.assertEqual(normalize_ingredient_name('Feta Cheese'), 'fetacheese')
        self.assertEqual(normalize_ingredient_name('Feta-Cheese'), 'fetacheese')

    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    def test_generate_html(self, mock_open):
        meals = [{'title': 'Test Meal', 'image': 'test.jpg', 'ingredients_present': ['feta'], 'missing_ingredients': ['eggplant'], 'nutrition': {'carbs': '20g', 'proteins': '10g', 'calories': '200'}}]
        filename = 'test.html'
        generate_html(meals, filename)
        mock_open.assert_called_once_with(filename, 'w', encoding='utf-8')
        handle = mock_open()
        handle.write.assert_called_once()
        self.assertIn('<html>', handle.write.call_args[0][0])
        self.assertIn('Test Meal', handle.write.call_args[0][0])

    # @patch('food_search.fetch_meals_from_api', return_value=[{'id': 1, 'title': 'Test Meal'}])
    # @patch('food_search.fetch_meal_details', return_value={'id': 1, 'title': 'Test Meal', 'image': 'test.jpg', 'extendedIngredients': [{'name': 'feta'}, {'name': 'eggplant'}]})
    # @patch('food_search.fetch_nutrition_details', return_value={'carbs': '20g', 'proteins': '10g', 'calories': '200'})
    # @patch('food_search.translate_to_polish', side_effect=lambda x: f"translated_{x}")
    # @patch('food_search.save_meal_to_db')
    # @patch('food_search.generate_html')
    # def test_find_food(self, mock_generate_html, mock_save_meal_to_db, mock_translate_to_polish, mock_fetch_nutrition_details, mock_fetch_meal_details, mock_fetch_meals_from_api):
    #     included_ingredients = ['feta', 'eggplant']
    #     excluded_ingredients = ['potato']
    #     find_food(included_ingredients, excluded_ingredients)
    #     mock_fetch_meals_from_api.assert_called_once_with(included_ingredients, excluded_ingredients)
    #     mock_fetch_meal_details.assert_called_once_with(1)
    #     mock_fetch_nutrition_details.assert_called_once_with(1)
    #     mock_translate_to_polish.assert_any_call('eggplant')
    #     mock_save_meal_to_db.assert_called_once()
    #     mock_generate_html.assert_called_once()
    #     self.assertEqual(mock_generate_html.call_args[0][1], 'eggplant_feta.html')

if __name__ == '__main__':
    unittest.main()
