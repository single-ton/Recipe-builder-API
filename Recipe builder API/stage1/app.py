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
error_response:dict

@app.route('/api/recipe', methods=['GET'])
def get_recipe():
    global current_recipe_obj
    error_response = {}
    if current_recipe_obj is None:
        error_response['error'] = "No recipe here yet"
        return json.dumps(error_response)
    else:
        error_response = dict
        error_response['error'] = "No recipe for these ingredients"
        if 'ingredients' not in request.args:
            return json.dumps(error_response)
        ingredients = request.args['ingredients'].split('|')
        if len(ingredients) != len(current_recipe_obj.ingredients):
            return json.dumps(error_response)
        for ingredient in current_recipe_obj.ingredients:
            if ingredient not in ingredients:
                return json.dumps(error_response)
        return str(current_recipe_obj)

@app.route('/api/recipe', methods=['POST'])
def post_recipe():
    global current_recipe_obj
    if request.json!=None:
        current_recipe_obj = Recipe_info(request.json)
        return Response(status=204)
    else:
        Response(status=400)

# don't change the following way to run flask:
if __name__ == '__main__':
    if len(sys.argv) > 1:
        arg_host, arg_port = sys.argv[1].split(':')
        app.run(host=arg_host, port=arg_port)
    else:
        app.run()