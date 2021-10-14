import copy

from flask import Flask
import sys
from flask import request
import json
from flask import Response

class Ingredient:
    title: str
    amount: float
    measure: str
    def __eq__(self, other):
        if isinstance(other, Ingredient) == False:
            return False
        if self.title != other.title or self.amount != other.amount or self.measure != other.measure:
            return False
        else:
            return True
class Recipe_info:
    title = ''
    ingredients = []
    directions = ''
    def from_json(self, recipe: str):
        recipe_json = json.loads(recipe)
        self.title = recipe_json['title']
        self.directions = recipe_json['directions']
        self.ingredients = []
        for ingredient in recipe_json['ingredients']:
            i = Ingredient()
            i.title = ingredient['title']
            i.amount = ingredient['amount']
            i.measure = ingredient['measure']
            self.ingredients.append(i)
    def from_other_recipe(self, recipe):
        copy_other = copy.deepcopy(recipe)
        self.title = copy_other.title
        self.directions = copy_other.directions
        self.ingredients = copy_other.ingredients
    def __init__(self, recipe = None):
        if recipe is None:
            return
        if isinstance(recipe, str):
            self.from_json(recipe)
        elif isinstance(recipe, Recipe_info):
            self.from_other_recipe(recipe)
    def __eq__(self, other):
        if isinstance(other, Recipe_info):
            return False
        if self.title != other.title:
            return False
        if self.directions != other.directions:
            return False
        if len(self.ingredients) != len(other.ingredients):
            return False
        for ingredient1 in self.ingredients:
            flag = True
            for ingredient2 in other.ingredients:
                if ingredient1.title == ingredient2.title and ingredient1.measure == ingredient2.measure and ingredient1.amount == ingredient2.amount:
                    flag = False
                    break
            if flag:
                return False
        return True
    def __str__(self):
        return self.to_json()
    def to_json(self):
        recipe_dict = copy.deepcopy(self).__dict__
        recipe_dict['ingredient'] = []
        for ingredient in self.ingredients:
            ingredient.amount = float(ingredient.amount)
            recipe_dict['ingredient'].append((ingredient.__dict__))
        del recipe_dict['ingredients']
        recipe_dict['ingredients'] = recipe_dict.pop('ingredient')
        jsonStr = json.dumps(recipe_dict)
        return jsonStr
    def get_ingredients_url_parameters(self):
        return "|".join([ingredient.title for ingredient in self.ingredients])
class Recipe_info_with_id(Recipe_info) :
    id: int
    def __str__(self, without_id=True):
        if without_id:
            return self.to_json_without_id()
        else:
            return super.__str__()
    def from_other_recipe(self, recipe):
        copy_other = copy.deepcopy(recipe)
        self.title = copy_other.title
        self.directions = copy_other.directions
        self.ingredients = copy_other.ingredients
    def from_json(self, recipe: str):
        recipe_json = json.loads(recipe)
        self.title = recipe_json['title']
        self.directions = recipe_json['directions']
        self.ingredients = []
        for ingredient in recipe_json['ingredients']:
            i = Ingredient()
            i.title = ingredient['title']
            i.amount = ingredient['amount']
            i.measure = ingredient['measure']
            self.ingredients.append(i)
    def __init__(self, other=None, id=None):
        if other is None:
            return
        if isinstance(other, Recipe_info):
            self.from_other_recipe(other)
            self.id = id
        if isinstance(other, Recipe_info_with_id):
            self.from_other_recipe(other)
            self.id = other.id
        elif isinstance(other, str):
            recipe_json = json.loads(other)
            self.from_json(other)
            try:
                self.id = recipe_json['id']
            except:
                if id is not None:
                    self.id = id

    def to_json(self):
        recipe_dict = copy.deepcopy(self).__dict__
        recipe_dict['ingredient'] = []
        for ingredient in self.ingredients:
            ingredient.amount = float(ingredient.amount)
            recipe_dict['ingredient'].append((ingredient.__dict__))
        del recipe_dict['ingredients']
        recipe_dict['ingredients'] = recipe_dict.pop('ingredient')
        jsonStr = json.dumps(recipe_dict)
        return jsonStr
    def to_json_without_id(self):
        recipe_dict = copy.deepcopy(self).__dict__
        recipe_dict['ingredient'] = []
        for ingredient in self.ingredients:
            ingredient.amount = float(ingredient.amount)
            recipe_dict['ingredient'].append((ingredient.__dict__))
        del recipe_dict['ingredients']
        del recipe_dict['id']
        recipe_dict['ingredients'] = recipe_dict.pop('ingredient')
        jsonStr = json.dumps(recipe_dict)
        return jsonStr
    def get_ingredients_url_parameters(self):
        return "|".join([ingredient.title for ingredient in self.ingredients])

app = Flask(__name__)

recipes = []
current_index = 1
no_recipes_message = "No recipe here yet"
no_recipes_for_ingredients_message = "No recipe for these ingredients"

@app.route('/api/recipe', methods=['GET'])
def get_recipes_by_ingredients():
    global recipes, no_recipes_message, no_recipes_for_ingredients_message
    return_recipes=[]
    if len(recipes) == 0:
        return json.dumps({'error': no_recipes_message})
    else:
        if 'ingredients' not in request.args:
            return json.dumps({'error': no_recipes_for_ingredients_message})
        ingredients = request.args['ingredients'].split('|')
        for recipe in recipes:
            ingredients_current_recipe = recipe.get_ingredients_url_parameters().split('|')
            ingredient_exists = True
            for ingredient in ingredients_current_recipe:
                if ingredient not in ingredients:
                    ingredient_exists = False
                    break;

            if ingredient_exists:
                return_recipes.append(recipe)
        if len(return_recipes) != 0:
            return "["+','.join([str(r) for r in return_recipes])+"]"
        else:
            return json.dumps({'error': no_recipes_for_ingredients_message})

@app.route('/api/recipe/<id>', methods=['GET'])
def get_recipe_by_id(id):
    global recipes
    if len(recipes) == 0:
        return Response("recipe with this id not found", status=404)
    else:
        for recipe in recipes:
            if recipe.id == int(id):
                return recipe.to_json_without_id()
    return Response("recipe with this id not found", status=404)

@app.route('/api/recipe/new', methods=['POST'])
def add_recipe():
    global recipes
    global current_index
    if request.json!=None:
        recipes.append(Recipe_info_with_id(request.json, current_index))
        current_index += 1
        return "{{\"id\":{}}}".format(current_index-1)
    return Response("", status=404)


# don't change the following way to run flask:
if __name__ == '__main__':
    if len(sys.argv) > 1:
        arg_host, arg_port = sys.argv[1].split(':')
        app.run(host=arg_host, port=arg_port)
    else:
        app.run()