import asyncio
import copy
from hstest import FlaskTest, CheckResult, WrongAnswer
from hstest import dynamic_test
from hstest.dynamic.security.exit_handler import ExitHandler
import xml.etree.ElementTree as ET
import json
from pip._vendor import requests

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
    def __str__(self):
        return self.to_json()

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

    def __init__(self, recipe=None):
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

def recipes_from_xml(file_name:str):
    list_recipes = []
    xml_tree = ET.parse(file_name)
    root_el = xml_tree.getroot()
    for recipe_el in root_el:
        recipe = Recipe_info()
        recipe.title = recipe_el.attrib['title']
        recipe.directions = recipe_el.attrib['directions']
        ingredients = recipe_el.find("ingredients")
        recipe.ingredients = []
        for ingredient_el in ingredients:
            ingredient = Ingredient()
            ingredient.title = ingredient_el.text
            ingredient.amount = float(ingredient_el.attrib['amount'])
            ingredient.measure = ingredient_el.attrib['measure']
            recipe.ingredients.append(ingredient)
        list_recipes.append(recipe)
    return list_recipes

class FlaskProjectTest(FlaskTest):
    source = 'app'
    list_recipes = []
    list_added_recipes = []
    wrong_answers = \
        [
            "File 'recipes.xml' not exists, please reload the project",#0
            "{} route should return code 200, now code is {}", #1
            "{} {} key should be in the json response", #2
            "{} response should not be empty", #3
            "{} route should return '{}' if no recipes added, now '{}'", #4
            "{} route should return '{}' If not enough ingredients, now '{}'",  # 5
            "{} route should return json with 3 keys, now '{}'",  # 6
            "{} route should return correct json response, if recipe added, now response: '{}'",  # 7
            "{} route, id added recipe must be a digit", #8
            "{} route, id must not be static", #9
            "{} route, should return 404 status code if recipe with id={} not added, now status code is {}",  # 10
            "{} route should return a list of recipes that only require a list of ingredients",  # 11
            "{} route, {} from recipe should be '{}', now '{}'",  # 12
            "{} route, the number of ingredients in the recipe does not correspond to the original, now {}, expected {}",  # 13
            "{} route, one of the ingredients of the original recipe is not returned, title='{}', measure='{}', amount='{}'",  # 14

        ]
    links = \
        [
            "{}api/recipe",  # 0
            "{}api/recipe?ingredients={}",  # 1
            "{}api/recipe/new",  # 2
            "{}api/recipe/{}",  # 3
        ]
    strings = \
        [
            "No recipe here yet",  # 0
            "No recipe for these ingredients"  # 1
        ]
    json_responses = \
        [
            {"error": strings[0]},
            {"error": strings[1]}
        ]

    def my_init(self):
        try:
            self.list_recipes = recipes_from_xml("recipes.xml")
        except:
            raise WrongAnswer(self.wrong_answers[0])

    def __init__(self, source_name: str = ''):
        super().__init__(source_name)
        self.my_init()
    def check_recipes_str(self, recipes:list, content:str, recipe_added, enough_ingredients):
        if not content:
            raise WrongAnswer(self.wrong_answers[3].format(self.links[1].format("GET /", "...")))
        try:#check correct json format
            recipes_dict = json.loads(content)
        except:
            raise WrongAnswer(self.wrong_answers[7].format(self.links[1].format("GET /", "..."), content))
        if recipe_added and enough_ingredients:
            if len(recipes) != len(recipes_dict):
                raise WrongAnswer(self.wrong_answers[11].format(self.links[1].format("GET /", "...")))
            for recipe_dict in recipes_dict:
                if "title" in recipe_dict.keys() == False:
                    raise WrongAnswer(self.wrong_answers[2].format(self.links[1].format("GET /", "..."), "title"))
                if "directions" in recipe_dict.keys() == False:
                    raise WrongAnswer(self.wrong_answers[2].format(self.links[1].format("GET /", "..."), "directions"))
                if "ingredients" in recipe_dict.keys() == False:
                    raise WrongAnswer(self.wrong_answers[2].format(self.links[1].format("GET /", "..."), "ingredients"))
                if len(recipe_dict.keys()) > 3:
                    raise WrongAnswer(self.wrong_answers[6].format(self.links[1].format("GET /", "..."), len(recipe_dict.keys())))
        elif recipe_added == False:
            if recipes_dict != self.json_responses[0]:
                raise WrongAnswer(self.wrong_answers[4].format(self.links[1].format("GET /", "..."), str(self.json_responses[0]), content))
        elif recipe_added and not enough_ingredients:
            if recipes_dict != self.json_responses[1]:
                raise WrongAnswer(self.wrong_answers[5].format(self.links[1].format("GET /", "..."), str(self.json_responses[1]), content))

    async def test_get_recipe_by_ingredients(self, recipes: list, recipe_added=True, enough_ingredients=True):
        r = requests.get(self.links[1].format(self.get_url(), recipes[0].get_ingredients_url_parameters()))
        if r.status_code != 200:
            raise WrongAnswer(self.wrong_answers[1].format(self.links[1].format("GET /", "..."), r.status_code))
        content = r.content.decode('UTF-8')
        self.check_recipes_str(recipes, content, recipe_added, enough_ingredients)

    async def test_get_recipes_by_ingredients(self, recipes: list, recipe_added=True, enough_ingredients=True):
        ingredients_url_parameters = []
        for recipe in recipes:
            ingredients_url_parameters.append(recipe.get_ingredients_url_parameters())
        result_ingredients = []
        for ingredients in ingredients_url_parameters:
            for ingredient in ingredients.split('|'):
                if ingredient not in result_ingredients:
                    result_ingredients.append(ingredient)
        ingredients_parameters = "|".join(result_ingredients)


        r = requests.get(self.links[1].format(self.get_url(), ingredients_parameters))
        if r.status_code != 200:
            raise WrongAnswer(self.wrong_answers[1].format(self.links[1].format("GET /", "..."), r.status_code))
        content = r.content.decode('UTF-8')
        self.check_recipes_str(recipes, content, recipe_added, enough_ingredients)

    def check_recipe_str_get_by_id(self, recipe: Recipe_info, content: str, id:int):
        try:
            recipe_dict = json.loads(content)
        except:
            raise WrongAnswer(self.wrong_answers[7].format(self.links[3].format("GET /", id), content))
        if not content:
            raise WrongAnswer(self.wrong_answers[3].format(self.links[3].format("GET /", id)))
        if "title" in recipe_dict.keys() == False:
            raise WrongAnswer(self.wrong_answers[2].format(self.links[3].format("GET /", id), "title"))
        if "directions" in recipe_dict.keys() == False:
            raise WrongAnswer(self.wrong_answers[2].format(self.links[3].format("GET /", id), "directions"))
        if "ingredients" in recipe_dict.keys() == False:
            raise WrongAnswer(self.wrong_answers[2].format(self.links[3].format("GET /", id), "ingredients"))
        if len(recipe_dict.keys()) > 3:
            raise WrongAnswer(
                self.wrong_answers[6].format(self.links[3].format("GET /", id), len(recipe_dict.keys())))
        if recipe.title != recipe_dict['title']:
            raise WrongAnswer(self.wrong_answers[12].format(self.links[3].format("GET /", id), 'title', recipe.title, recipe_dict['title']))
        if recipe.directions != recipe_dict['directions']:
            raise WrongAnswer(self.wrong_answers[12].format(self.links[3].format("GET /", id), 'directions', recipe.directions, recipe_dict['directions']))
        link = self.links[3].format("GET /", id)
        if len(recipe.ingredients) != len(recipe_dict['ingredients']):
            raise WrongAnswer(self.wrong_answers[13].format(link, len(recipe_dict['ingredient']), len(recipe.ingredients)))
        self.check_ingredients(recipe.ingredients, recipe_dict['ingredients'], id)
    def check_ingredients(self, recipe_ingredients:list, json_ingredients:list, id):
        for ingredient_recipe in recipe_ingredients:
            flag_exists = False
            for ingredient_json in json_ingredients:
                if ingredient_json['title'] == ingredient_recipe.title\
                        and ingredient_json['measure'] == ingredient_recipe.measure\
                        and str(ingredient_json['amount']) == str(ingredient_recipe.amount):
                    flag_exists = True
                    break
            if not flag_exists:
                raise WrongAnswer(self.wrong_answers[14].format(self.links[3].format("GET /", id), ingredient_recipe.title, ingredient_recipe.measure, ingredient_recipe.amount))

    async def test_get_recipe_by_id(self, id:int, recipe_added=False, recipe: Recipe_info=None):
        r = requests.get(self.links[3].format(self.get_url(), id))
        if not recipe_added:
            if r.status_code != 404:
                raise WrongAnswer(self.wrong_answers[10].format(self.links[3].format(self.get_url(), id), id, r.status_code))
        else:
            content = r.content.decode("UTF-8")
            self.check_recipe_str_get_by_id(recipe, content, id)
    def check_post_recipe_respond(self, content):
        if not content:
            raise WrongAnswer(self.wrong_answers[7].format(self.links[2].format("POST /", ), content))
        try:
            json_dict = json.loads(content)
        except:
            raise WrongAnswer(self.wrong_answers[7].format(self.links[2].format("POST /"), content))
        if "id" not in json_dict.keys():
            raise WrongAnswer(self.wrong_answers[2].format(self.links[2].format("POST /"), "id"))
        if len(json_dict.keys()) > 1:
            raise WrongAnswer(self.wrong_answers[6].format(self.links[1].format("GET /", "..."), len(json_dict.keys())))
        if not str(json_dict['id']).isdigit() and str(int(json_dict['id'])) == str(json_dict['id']):
            raise WrongAnswer(self.wrong_answers[8].format(self.links[2].format("POST /")))
        if len(self.list_recipes) != 0:
            for recipe in self.list_added_recipes:
                if recipe.id == int(json_dict['id']):
                    raise WrongAnswer(self.wrong_answers[9].format(self.links[2].format("POST /")))

    async def test_post_recipe(self, recipe:Recipe_info):
        r = requests.post(self.links[2].format(self.get_url()), json=str(recipe))
        if r.status_code != 200:
            raise WrongAnswer(self.wrong_answers[1].format(self.links[0].format("POST /"), r.status_code))
        content = r.content.decode("UTF-8")
        self.check_post_recipe_respond(content)
        json_dict = json.loads(content)
        self.list_added_recipes.append(Recipe_info_with_id(recipe, int(json_dict['id'])))

    @dynamic_test(order=1)
    def test1(self):
        ExitHandler.revert_exit()
        print("Get recipe by ingredients, no recipe added")
        asyncio.get_event_loop().run_until_complete(self.test_get_recipe_by_ingredients([self.list_recipes[0]], False, False))
        return CheckResult.correct()

    @dynamic_test(order=2)
    def test2(self):
        ExitHandler.revert_exit()
        print("Add recipe")
        asyncio.get_event_loop().run_until_complete(self.test_post_recipe(self.list_recipes[0]))
        return CheckResult.correct()

    @dynamic_test(order=3)
    def test3(self):
        ExitHandler.revert_exit()
        print("Get recipe by added recipe ingredients")
        asyncio.get_event_loop().run_until_complete(self.test_get_recipe_by_ingredients([self.list_recipes[0]], True, True))
        return CheckResult.correct()

    @dynamic_test(order=4)
    def test4(self):
        ExitHandler.revert_exit()
        print("Get recipe by invalid recipe ingredients")
        asyncio.get_event_loop().run_until_complete(self.test_get_recipe_by_ingredients([self.list_recipes[1]], True, False))
        return CheckResult.correct()

    @dynamic_test(order=5)
    def test5(self):
        ExitHandler.revert_exit()
        print("Add 2 recipe")
        asyncio.get_event_loop().run_until_complete(self.test_post_recipe(self.list_recipes[3]))
        return CheckResult.correct()

    @dynamic_test(order=6)
    def test6(self):
        ExitHandler.revert_exit()
        print("Get recipes by 2 recipe ingredients")
        asyncio.get_event_loop().run_until_complete(self.test_get_recipe_by_ingredients([self.list_recipes[3]], True, True))
        return CheckResult.correct()

    @dynamic_test(order=7)
    def test7(self):
        ExitHandler.revert_exit()
        print("Get recipes by added ingredients")
        asyncio.get_event_loop().run_until_complete(
            self.test_get_recipes_by_ingredients([self.list_recipes[3], self.list_recipes[0]], True, True))
        return CheckResult.correct()

    @dynamic_test(order=8)
    def test8(self):
        ExitHandler.revert_exit()
        print("Get recipe by invalid recipe ingredients")
        asyncio.get_event_loop().run_until_complete(self.test_get_recipe_by_ingredients([self.list_recipes[4]], True, False))
        return CheckResult.correct()

    @dynamic_test(order=9)
    def test9(self):
        ExitHandler.revert_exit()
        print("Get recipe by invalid id")
        asyncio.get_event_loop().run_until_complete(self.test_get_recipe_by_id(99))
        return CheckResult.correct()

    @dynamic_test(order=10)
    def test10(self):
        ExitHandler.revert_exit()
        print("Get recipe valid id, from added recipe")
        asyncio.get_event_loop().run_until_complete(self.test_get_recipe_by_id(self.list_added_recipes[0].id, True, self.list_added_recipes[0]))
        return CheckResult.correct()

    @dynamic_test(order=11)
    def test11(self):
        ExitHandler.revert_exit()
        print("Get another recipe valid id, from added recipe")
        asyncio.get_event_loop().run_until_complete(
            self.test_get_recipe_by_id(self.list_added_recipes[1].id, True, self.list_added_recipes[1]))
        return CheckResult.correct()


if __name__ == '__main__':
    FlaskProjectTest().run_tests()