import copy
from flask_sqlalchemy import SQLAlchemy
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
    def __init__(self, recipe = None, ingredients=None):
        if recipe is None:
            return
        if isinstance(recipe, str):
            self.from_json(recipe)
        elif isinstance(recipe, Recipe_info):
            self.from_other_recipe(recipe)
        elif isinstance(recipe, Recipe) and isinstance(ingredients, list):
            self.title = recipe.title
            self.directions = recipe.directions
            self.ingredients = []
            for ingredient in ingredients:
                ingredient_buf = Ingredient()
                ingredient_buf.title = ingredient.title
                ingredient_buf.amount = ingredient.amount
                ingredient_buf.measure = ingredient.measure
                self.ingredients.append(ingredient_buf)
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
    def to_json_with_id(self, id):
        recipe_dict = copy.deepcopy(self).__dict__
        recipe_dict['ingredient'] = []
        for ingredient in self.ingredients:
            ingredient.amount = float(ingredient.amount)
            recipe_dict['ingredient'].append((ingredient.__dict__))
        del recipe_dict['ingredients']
        recipe_dict['id'] = id
        recipe_dict['ingredients'] = recipe_dict.pop('ingredient')
        jsonStr = json.dumps(recipe_dict)
        return jsonStr
    def get_ingredients_url_parameters(self):
        return "|".join([ingredient.title for ingredient in self.ingredients])




app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///recipes.db'
db = SQLAlchemy(app)

no_recipes_message = "No recipe here yet"
no_recipes_for_ingredients_message = "No recipe for these ingredients"

class Recipe(db.Model):
    def __init__(self, recipe: str = None):
        if recipe is None:
            return
        if isinstance(recipe, str):
            json_recipe = json.loads(recipe)
            self.title = json_recipe['title']
            self.directions = json_recipe['directions']

    __tablename__ = "recipe"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    directions = db.Column(db.String(80), nullable=False)

class Ingredientdb(db.Model):
    __tablename__ = "ingredient"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    measure = db.Column(db.String(10), nullable=False)
    amount = db.Column(db.Float, nullable=False)

    def __eq__(self, other):
        if isinstance(other, Ingredient):
            if other.title == self.title and other.measure == self.measure and other.amount == self.amount:
                return True
        elif isinstance(other, Ingredientdb):
            if other.title == self.title and other.measure == self.measure and other.amount == self.amount:
                return True
        return False

class Recipe_has_ingredient(db.Model):
    __tablename__ = "recipe_has_product"

    def __init__(self, id_ingredient=None, id_recipe=None):
        if id_ingredient is None:
            return
        self.id_ingredient = id_ingredient
        self.id_recipe = id_recipe

    id = db.Column(db.Integer, primary_key=True)
    id_ingredient = db.Column(db.Integer, db.ForeignKey('ingredient.id'), nullable=False)
    id_recipe = db.Column(db.Integer, db.ForeignKey('recipe.id'), nullable=False)

db.create_all()


@app.route('/api/recipe', methods=['GET'])
def get_recipe_by_ingredients():
    global db, no_recipes_message, no_recipes_for_ingredients_message
    recipes = Recipe.query.all()
    if len(Recipe.query.all()) == 0:
        return json.dumps({'error': no_recipes_message})
    else:
        if 'ingredients' not in request.args:
            return json.dumps({'error': no_recipes_for_ingredients_message})
        ingredients = request.args['ingredients'].split('|')
        recipe_found = False
        for recipe_db in recipes:
            ingredients_query = db.session.query(Recipe_has_ingredient, Ingredientdb
                                                 ).filter(Recipe_has_ingredient.id_recipe == recipe_db.id
                                                          ).filter(
                Ingredientdb.id == Recipe_has_ingredient.id_ingredient).all()
            ingredients_from_base = []
            for ingredient in ingredients_query:
                ingredients_from_base.append(ingredient[1])
            breaked = False
            if len(ingredients) == len(ingredients_query):
                for ingredient in ingredients_from_base:
                    if ingredient.title not in ingredients:
                        breaked = True
                        break
                if breaked == False:
                    recipe_found = True
            if recipe_found:
                return "["+Recipe_info(recipe_db, ingredients_from_base).to_json_with_id(recipe_db.id)+"]"
        return json.dumps({'error': no_recipes_for_ingredients_message})


@app.route('/api/recipe/<id>', methods=['DELETE'])
def delete(id):
    global db
    recipe = Recipe.query.get(id)
    if recipe is None:
        return Response(status=404)
    else:
        db.session.delete(recipe)
        db.session.commit()
        return Response(status=204)

@app.route('/api/recipe/<id>', methods=['GET'])
def get_recipe_by_id(id):
    recipe = Recipe.query.get(id)
    if recipe is None:
        return Response(status=404)
    else:
        ingredients_query = db.session.query(Recipe_has_ingredient, Ingredientdb
                                             ).filter(Recipe_has_ingredient.id_recipe == recipe.id
                                                      ).filter(
            Ingredientdb.id == Recipe_has_ingredient.id_ingredient).all()
        ingredients_from_base = []
        for ingredient in ingredients_query:
            ingredients_from_base.append(ingredient[1])
        return Recipe_info(recipe, ingredients_from_base).to_json()

@app.route('/api/recipe/new', methods=['POST'])
def add_recipe():
    global db
    if request.json != None:
        try:
            recipe_json = json.loads(request.json)
            s = recipe_json['directions']
            if s == "": raise ValueError
            s = recipe_json['title']
            if s == "": raise ValueError
            if len(recipe_json['ingredients']) == 0: raise ValueError
        except:
            return Response(status=400)
        r = Recipe(request.json)
        db.session.add(r)
        db.session.commit()
        ingredients = []
        for ingredient_json in recipe_json['ingredients']:
            ingredient = Ingredientdb(title=ingredient_json['title'], measure=ingredient_json['measure'],
                                      amount=ingredient_json['amount'])
            ingredients.append(ingredient)
            db.session.add(ingredient)
        db.session.commit()
        recipe_has_ingredients = []
        for ingredient in ingredients:
            rh = Recipe_has_ingredient(id_ingredient=ingredient.id, id_recipe=r.id)
            recipe_has_ingredients.append(rh)
            db.session.add(rh)
        db.session.commit()
        return "{{\"id\":{}}}".format(r.id)
    return Response("", status=404)


# don't change the following way to run flask:
if __name__ == '__main__':
    if len(sys.argv) > 1:
        arg_host, arg_port = sys.argv[1].split(':')
        app.run(host=arg_host, port=arg_port)
    else:
        app.run()