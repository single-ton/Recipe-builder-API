import copy
from flask_sqlalchemy import SQLAlchemy
from flask import Flask
import sys
from flask import request
import json
from flask import Response
from sqlalchemy import update
from sqlalchemy.ext.hybrid import hybrid_property

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
    directions = []
    description = ''

    def __lt__(self, other):
        return self.title < other.title
    def __init__(self, recipe=None, ingredients=None):

        if recipe is None:
            return
        if isinstance(recipe, str):
            recipe_json = json.loads(recipe)
            self.title = recipe_json['title']
            self.directions=[]
            for direction in recipe_json['directions']:
                self.directions.append(direction)
            self.description = recipe_json['description']
            self.ingredients = []
            for ingredient in recipe_json['ingredients']:
                i = Ingredient()
                i.title = ingredient['title']
                i.amount = ingredient['amount']
                i.measure = ingredient['measure']
                self.ingredients.append(i)
        elif isinstance(recipe, Recipe_info):
            copy_other = copy.deepcopy(recipe)
            self.title = copy_other.title
            self.directions = copy_other.directions
            self.ingredients = copy_other.ingredients
        elif isinstance(recipe, Recipe) and isinstance(ingredients, list):
            self.title = recipe.title
            self.description = recipe.description
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
        if len(self.directions) != len(other.directions):
            return False
        for direction in self.directions:
            if direction not in other.directions:
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
    def __str__(self):
        return self.to_json()
    def get_ingredients_url_parameters(self):
        return "|".join([ingredient.title for ingredient in self.ingredients])



app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///recipes.db'
db = SQLAlchemy(app)


class Recipe(db.Model):
    def __repr__(self):
        return repr((self.title))
    def __init__(self, recipe=None):
        if recipe is None:
            return
        if isinstance(recipe, str):
            json_recipe = json.loads(recipe)
            self.title = json_recipe['title']
            self.description = json_recipe['description']
            self._directions = ""
            for direction in json_recipe['directions']:
                if self._directions == "":
                    self._directions = direction
                else:
                    self._directions = self._directions + "|" + direction
        if isinstance(recipe, Recipe_info):
            self.title = recipe.title
            self.description = recipe.description
            self._directions = ""
            for direction in recipe.directions:
                if self._directions == "":
                    self._directions = direction
                else:
                    self._directions = self._directions + "|" + direction

    __tablename__ = "recipe"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    _directions = db.Column(db.String(500), nullable=False)
    description = db.Column(db.String(80), nullable=False)

    @hybrid_property
    def directions(self):
        return str(self._directions).split('|')

    @hybrid_property
    def directions_original(self):
        return self._directions


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


@app.route('/api/recipe/<id>', methods=['DELETE'])
def delete_recipe_by_id(id):
    global db
    recipe = Recipe.query.get(id)
    if recipe is None:
        return Response(status=404)
    else:
        db.session.delete(recipe)
        db.session.commit()
        return Response(status=204)

@app.route('/api/recipe/<id>', methods=['PUT'])
def put_recipe_by_id(id):
    global db
    recipe = Recipe.query.get(id)
    if recipe is None:
        return Response(status=404)
    else:
        if request.json != None:
            try:
                recipe_json = json.loads(request.json)
                d = recipe_json['directions']
                if len(d) == 0: raise ValueError
                s = recipe_json['title']
                if s == "": raise ValueError
                if len(recipe_json['ingredients']) == 0: raise ValueError
            except:
                return Response(status=400)
            recipe_from_put = Recipe_info(request.json)
            recipe_db = Recipe(recipe_from_put)
            recipe_from_db = Recipe.query.get(id)
            stmt = update(Recipe).where(Recipe.id == id).\
                values(title=recipe_db.title, description=recipe_db.description, _directions=recipe_db.directions_original). \
                execution_options(synchronize_session="fetch")
            result = db.session.execute(stmt)
            recipe_ingredients_query = db.session.query(Recipe_has_ingredient, Ingredientdb
                 ).filter(Recipe_has_ingredient.id_recipe == id
                  ).filter(Ingredientdb.id == Recipe_has_ingredient.id_ingredient).all()
            for d in recipe_ingredients_query:
                db.session.delete(d[0])
            for d in recipe_ingredients_query:
                db.session.delete(d[1])
            db.session.commit()
            ingredients=[]
            for ingredient_put in recipe_from_put.ingredients:
                ingredient = Ingredientdb(title=ingredient_put.title, measure=ingredient_put.measure,
                                          amount=ingredient_put.amount)
                ingredients.append(ingredient)
                db.session.add(ingredient)
            db.session.commit()
            recipe_has_ingredients = []
            for ingredient in ingredients:
                rh = Recipe_has_ingredient(id_ingredient=ingredient.id, id_recipe=id)
                recipe_has_ingredients.append(rh)
                db.session.add(rh)
            db.session.commit()
            return Response(status=204)
        else:
            return Response("", status=400)

@app.route('/api/recipe', methods=['GET'])
def get_recipe_by_ingredients():
    global db
    recipes = Recipe.query.all()
    if len(Recipe.query.all()) == 0:
        return "No recipe here yet"
    else:
        if 'ingredients' not in request.args:
            return "No recipe for these ingredients"
        if 'max_directions' in request.args:
            new_recipes=[]
            max_directions = request.args['max_directions']
            for recipe in recipes:
                if len(recipe.directions) <= int(max_directions):
                    new_recipes.append(recipe)
            recipes = new_recipes
        ingredients = request.args['ingredients'].split('|')
        recipe_found = False
        found_recipes = []
        found_ingredients=[]
        for recipe_db in recipes:
            ingredients_query = db.session.query(Recipe_has_ingredient, Ingredientdb
                                                 ).filter(Recipe_has_ingredient.id_recipe == recipe_db.id
                                                          ).filter(
                Ingredientdb.id == Recipe_has_ingredient.id_ingredient).all()
            ingredients_from_base = []
            for ingredient in ingredients_query:
                ingredients_from_base.append(ingredient[1])
            breaked = False
            if len(ingredients) >= len(ingredients_query):
                for ingredient in ingredients_from_base:
                    if ingredient.title not in ingredients:
                        breaked = True
                        break
                if breaked == False:
                    recipe_found = True
            if recipe_found:
                found_recipes.append(recipe_db)
                found_ingredients.append(ingredients_from_base)
        if len(found_recipes) != 0:
            list_recipes = []
            for recipe, ingredient in zip(found_recipes, found_ingredients):
                list_recipes.append(Recipe_info(recipe, ingredient))
            list_recipes.sort( reverse=True)
            return "["+','.join([str(recipe) for recipe in list_recipes])+"]"
        return "[]"

@app.route('/api/recipe/<id>', methods=['GET'])
def get_recipe_by_id(id):
    recipe = Recipe.query.get(id)
    if recipe is None:
        return Response("recipe with this id not found", status=404)
    else:
        ingredients_query = db.session.query(Recipe_has_ingredient, Ingredientdb
            ).filter(Recipe_has_ingredient.id_recipe == recipe.id
            ).filter(Ingredientdb.id == Recipe_has_ingredient.id_ingredient).all()
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
            d = recipe_json['directions']
            if len(d) == 0: raise ValueError
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