# foodapp

### Running the Script
1. Change the food preferences in the main function of the food_search.py file
2. Open a terminal or command prompt.
3. Navigate to the directory where you have cloned or downloaded this repository.
4. Install requirements:
```bash
if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
```
5. Setup the database using the following command:

```bash
python3 setup_database.py
```
5. Run the script using the following command:
   
```bash
python3 food_search.py
```
After executing this command html file with recipes should appear in your directory
### Executing the unittests
1. Open a terminal or command prompt.
2. Navigate to the directory where you have cloned or downloaded this repository.
3. Execute the tests using the following command:

```bash
python3 -m unittest test_food_search.py
```
