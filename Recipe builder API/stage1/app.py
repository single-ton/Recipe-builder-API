import copy
from flask import Flask
import sys
from flask import request
from flask import Response
import json

class Recipe_info:
    title = ''
    ingredients = []
    directions = ''
    def from_json(self, recipe:str):
        recipe_json = json.loads(recipe)
        self.title = recipe_json['title']
        self.directions = recipe_json['directions']
        self.ingredients = []
        for ingredient in recipe_json['ingredients']:
            self.ingredients.append(ingredient)
    def to_json(self):
        recipe_dict = copy.deepcopy(self).__dict__
        recipe_dict['ingredient'] = []
        for ingredient in self.ingredients:
            recipe_dict['ingredient'].append(ingredient)
        del recipe_dict['ingredients']
        recipe_dict['ingredients'] = recipe_dict.pop('ingredient')
        jsonStr = json.dumps(recipe_dict)
        return jsonStr
    def get_ingredients_url_parameters(self):
        return "|".join([ingredient for ingredient in self.ingredients])
    def __str__(self):
        return self.to_json()
    def __init__(self, recipe=None):
        if recipe is None:
            return
        if isinstance(recipe, str):
            self.from_json(recipe)


app = Flask(__name__)
current_recipe_obj:Recipe_info = None
no_recipes_message = "No recipe here yet"
no_recipes_for_ingredients_message = "No recipe for these ingredients"

@app.route('/api/recipe', methods=['GET'])
def get_recipe():
    global no_recipes_message, no_recipes_for_ingredients_message, current_recipe_obj
    if current_recipe_obj is None:
        return json.dumps({'error': no_recipes_message})
    else:
        if 'ingredients' not in request.args:
            return json.dumps({'error': no_recipes_for_ingredients_message})
        ingredients = request.args['ingredients'].split('|')
        if len(ingredients) != len(current_recipe_obj.ingredients):
            return json.dumps({'error': no_recipes_for_ingredients_message})
        for ingredient in current_recipe_obj.ingredients:
            if ingredient not in ingredients:
                return json.dumps({'error': no_recipes_for_ingredients_message})
        return str(current_recipe_obj)

@app.route('/api/recipe', methods=['POST'])
def post_recipe():
    global current_recipe_obj
    if request.json!=None:
        try:
            current_recipe_obj = Recipe_info(request.json)
            return Response(status=204)
        except: return Response(status=400)

    else:
        return Response(status=400)

# don't change the following way to run flask:
if __name__ == '__main__':
    if len(sys.argv) > 1:
        arg_host, arg_port = sys.argv[1].split(':')
        app.run(host=arg_host, port=arg_port)
    else:
        app.run()