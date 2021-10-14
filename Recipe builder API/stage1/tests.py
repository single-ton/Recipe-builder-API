import asyncio
import copy
from hstest import FlaskTest, CheckResult, WrongAnswer
from hstest import dynamic_test
from hstest.dynamic.security.exit_handler import ExitHandler
import xml.etree.ElementTree as ET
import json
from pip._vendor import requests

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
            recipe.ingredients.append(ingredient_el.text)
        list_recipes.append(recipe)
    return list_recipes

class FlaskProjectTest(FlaskTest):
    source = 'app'
    list_recipes = []
    wrong_answers = \
        [
            "File 'recipes.xml' not exists or incorrect format, please reload the project",#0
            "{} route should return code 200, now status code is {}", #1
            "{} {} key should be in the json response", #2
            "{} response should not be empty", #3
            "{} route should return '{}' if no recipes added, now '{}'", #4
            "{} route should return '{}' If not enough ingredients, now '{}'",  # 5
            "{} route should return json with 3 keys, now '{}'",  # 6
            "{} route should return correct json response, if recipe added, now response: '{}'",  # 7
        ]
    links = \
    [
        "{}api/recipe", #0
        "{}api/recipe?ingredients={}", #1

    ]
    strings = \
    [
        "No recipe here yet", #0
        "No recipe for these ingredients" #1
    ]

    def my_init(self):
        try:
            self.list_recipes = recipes_from_xml("recipes.xml")
        except:
            raise WrongAnswer(self.wrong_answers[0])

    def __init__(self, source_name: str = ''):
        super().__init__(source_name)
        self.my_init()
    def check_recipe_str(self, recipe:Recipe_info, content:str, recipe_added, enough_ingredients):
        if recipe_added and enough_ingredients:
            try:
                recipe_dict = json.loads(content)
            except:
                raise WrongAnswer(self.wrong_answers[7].format(self.links[1].format("GET /", "..."), content))
            if not content:
                raise WrongAnswer(self.wrong_answers[3].format(self.links[1].format("GET /", "...")))
            if "title" in recipe_dict.keys() == False:
                raise WrongAnswer(self.wrong_answers[2].format(self.links[1].format("GET /", "..."), "title"))
            if "directions" in recipe_dict.keys() == False:
                raise WrongAnswer(self.wrong_answers[2].format(self.links[1].format("GET /", "..."), "directions"))
            if "ingredients" in recipe_dict.keys() == False:
                raise WrongAnswer(self.wrong_answers[2].format(self.links[1].format("GET /", "..."), "ingredients"))
            if len(recipe_dict.keys()) > 3:
                raise WrongAnswer(self.wrong_answers[6].format(self.links[1].format("GET /", "..."), len(recipe_dict.keys())))
        elif recipe_added == False:
            if self.strings[0] != content:
                raise WrongAnswer(self.wrong_answers[4].format(self.links[1].format("GET /", "..."), self.strings[0], content))
        elif recipe_added and enough_ingredients == False:
            if self.strings[1] != content:
                raise WrongAnswer(self.wrong_answers[5].format(self.links[1].format("GET /", "..."), self.strings[1], content))

    async def test_get_recipe(self, recipe:Recipe_info, recipe_added=True, enough_ingredients = True):
        r = requests.get(self.links[1].format(self.get_url(), recipe.get_ingredients_url_parameters()))
        if r.status_code != 200:
            raise WrongAnswer(self.wrong_answers[1].format(self.links[1].format("GET /", "..."), r.status_code))
        content = r.content.decode('UTF-8')
        self.check_recipe_str(recipe, content, recipe_added, enough_ingredients)

    async def test_post_recipe(self, recipe:Recipe_info):
        r = requests.post(self.links[0].format(self.get_url()), json=str(recipe))
        if r.status_code != 204:
            raise WrongAnswer(self.wrong_answers[1].format(self.links[1].format("POST /", "..."), r.status_code))

    @dynamic_test(order=1)
    def test1(self):
        ExitHandler.revert_exit()
        asyncio.get_event_loop().run_until_complete(self.test_get_recipe(self.list_recipes[0], False, False))
        return CheckResult.correct()

    @dynamic_test(order=2)
    def test2(self):
        ExitHandler.revert_exit()
        asyncio.get_event_loop().run_until_complete(self.test_post_recipe(self.list_recipes[0]))
        return CheckResult.correct()

    @dynamic_test(order=3)
    def test3(self):
        ExitHandler.revert_exit()
        asyncio.get_event_loop().run_until_complete(self.test_get_recipe(self.list_recipes[0], True, True))
        return CheckResult.correct()

    @dynamic_test(order=4)
    def test4(self):
        ExitHandler.revert_exit()
        asyncio.get_event_loop().run_until_complete(self.test_get_recipe(self.list_recipes[1], True, False))
        return CheckResult.correct()

    @dynamic_test(order=5)
    def test5(self):
        ExitHandler.revert_exit()
        asyncio.get_event_loop().run_until_complete(self.test_post_recipe(self.list_recipes[3]))
        return CheckResult.correct()

    @dynamic_test(order=6)
    def test6(self):
        ExitHandler.revert_exit()
        asyncio.get_event_loop().run_until_complete(self.test_get_recipe(self.list_recipes[3], True, True))
        return CheckResult.correct()


if __name__ == '__main__':
    FlaskProjectTest().run_tests()