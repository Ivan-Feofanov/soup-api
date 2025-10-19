from django.test import TestCase, Client

from users.models import CustomUser
from kitchen.models import Ingredient, Unit, Recipe, RecipeIngredient


class KitchenControllerTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Create a user
        self.password = "pass1234!"
        self.user = CustomUser.objects.create_user(
            email="chef@example.com",
            password=self.password,
            username="chef",
            handler="chef-handler",
        )
        self.token = self._obtain_access_token(self.user.email, self.password)
        # Another user to test forbidden updates
        self.other_user = CustomUser.objects.create_user(
            email="intruder@example.com", password=self.password
        )
        # Create base units and ingredients
        self.unit_g = Unit.objects.create(name="Gram", abbreviation="g")
        self.unit_ml = Unit.objects.create(name="Milliliter", abbreviation="ml")
        self.ing_flour = Ingredient.objects.create(name="Flour")
        self.ing_water = Ingredient.objects.create(name="Water")

        # Create a recipe for list/get endpoints
        self.recipe = Recipe.objects.create(
            author=self.user,
            title="Bread",
            description="Simple bread",
            instructions=["Mix", "Bake"],
        )
        RecipeIngredient.objects.create(
            recipe=self.recipe,
            ingredient=self.ing_flour,
            unit=self.unit_g,
            quantity=500,
        )
        RecipeIngredient.objects.create(
            recipe=self.recipe,
            ingredient=self.ing_water,
            unit=self.unit_ml,
            quantity=300,
        )

    def _obtain_access_token(self, email: str, password: str) -> str:
        url = "/api/token/pair"
        resp = self.client.post(
            url,
            data={"email": email, "password": password},
            content_type="application/json",
        )
        self.assertEqual(
            resp.status_code, 200, msg=f"Token pair failed: {resp.content}"
        )
        data = resp.json()
        self.assertIn("access", data)
        return data["access"]

    def test_list_recipes(self):
        resp = self.client.get("/api/kitchen/recipes/")
        data = resp.json()

        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 1)
        first = data[0]
        self.assertEqual(first["name"], "Bread")
        # Author block
        self.assertIn("author", first)
        self.assertEqual(first["author"]["email"], self.user.email)
        # Ingredients resolved with unit abbreviation and quantity
        self.assertIn("ingredients", first)
        ing_names = sorted(i["name"] for i in first["ingredients"])  # type: ignore
        self.assertEqual(ing_names, ["Flour", "Water"])
        units = sorted(i["unit"] for i in first["ingredients"])  # type: ignore
        self.assertEqual(sorted(units), ["g", "ml"])

    def test_get_recipe(self):
        resp = self.client.get(f"/api/kitchen/recipes/{self.recipe.uid}")
        data = resp.json()

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(data["uid"], str(self.recipe.uid))
        self.assertEqual(data["title"], "Bread")
        self.assertEqual(data["description"], "Simple bread")
        self.assertEqual(data["instructions"], ["Mix", "Bake"])
        self.assertEqual(data["notes"], None)
        self.assertEqual(data["image"], None)
        # Ingredients resolved with unit abbreviation and quantity
        self.assertEqual(len(data["ingredients"]), 2)
        self.assertEqual(data["ingredients"][0]["quantity"], 500)
        self.assertEqual(
            data["ingredients"][0]["ingredient"]["uid"], str(self.ing_flour.uid)
        )
        self.assertEqual(data["ingredients"][0]["ingredient"]["name"], "Flour")
        self.assertEqual(data["ingredients"][0]["unit"]["uid"], str(self.unit_g.uid))
        self.assertEqual(data["ingredients"][0]["unit"]["abbreviation"], "g")
        self.assertEqual(data["ingredients"][0]["unit"]["name"], "Gram")
        self.assertEqual(data["ingredients"][1]["quantity"], 300)
        self.assertEqual(
            data["ingredients"][1]["ingredient"]["uid"], str(self.ing_water.uid)
        )
        self.assertEqual(data["ingredients"][1]["ingredient"]["name"], "Water")
        self.assertEqual(data["ingredients"][1]["unit"]["uid"], str(self.unit_ml.uid))
        self.assertEqual(data["ingredients"][1]["unit"]["abbreviation"], "ml")
        self.assertEqual(data["ingredients"][1]["unit"]["name"], "Milliliter")
        # Author block
        self.assertIn("author", data)
        self.assertEqual(data["author"]["email"], self.user.email)

    def test_list_ingredients(self):
        resp = self.client.get("/api/kitchen/ingredients/")
        data = resp.json()

        self.assertEqual(resp.status_code, 200)
        names = sorted(d["name"] for d in data)
        # Our two and anything else created elsewhere
        self.assertTrue({"Flour", "Water"}.issubset(set(names)))

    def test_list_units(self):
        resp = self.client.get("/api/kitchen/units/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        abbrevs = [d["abbreviation"] for d in data]
        self.assertIn("g", abbrevs)
        self.assertIn("ml", abbrevs)

    def test_create_ingredient(self):
        url = "/api/kitchen/ingredients/"
        payload = {"name": "Sugar"}

        resp = self.client.post(
            url,
            data=payload,
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )
        data = resp.json()

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(data["name"], "Sugar")
        self.assertTrue(Ingredient.objects.filter(name="Sugar").exists())

    def test_create_ingredient_idempotent_by_name(self):
        url = "/api/kitchen/ingredients/"
        payload = {"name": "Sugar"}
        r1 = self.client.post(
            url,
            data=payload,
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )
        first_uid = r1.json()["uid"]

        # Posting same name should return existing ingredient (same uid)
        r2 = self.client.post(
            url,
            data=payload,
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )

        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.json()["uid"], first_uid)
        self.assertEqual(Ingredient.objects.filter(name="Sugar").count(), 1)

    def test_create_recipe_non_auth(self):
        url = "/api/kitchen/recipes/"
        payload = {
            "title": "Pancakes",
            "description": "Yummy",
            "image": None,
            "notes": None,
            "instructions": ["Mix", "Fry"],
            "ingredients": [
                {
                    "ingredient_uid": str(self.ing_flour.uid),
                }
            ],
        }
        r = self.client.post(url, data=payload, content_type="application/json")
        self.assertEqual(r.status_code, 401)

    def test_create_recipe(self):
        url = "/api/kitchen/recipes/"
        payload = {
            "title": "Pancakes",
            "description": "Yummy",
            "image": None,
            "notes": None,
            "instructions": ["Mix", "Fry"],
            "ingredients": [
                {
                    "ingredient_uid": str(self.ing_flour.uid),
                    "unit_uid": str(self.unit_g.uid),
                    "quantity": 100,
                }
            ],
        }

        response = self.client.post(
            url,
            data=payload,
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )
        data = response.json()

        self.assertEqual(response.status_code, 200, msg=response.content)
        self.assertEqual(data["title"], "Pancakes")
        self.assertEqual(len(data["ingredients"]), 1)
        # DB side checks
        self.assertTrue(
            Recipe.objects.filter(title="Pancakes", author=self.user).exists()
        )
        new_recipe = Recipe.objects.get(title="Pancakes")
        self.assertEqual(new_recipe.recipeingredient_set.count(), 1)
        self.assertEqual(
            new_recipe.recipeingredient_set.first().ingredient, self.ing_flour
        )
        self.assertEqual(new_recipe.recipeingredient_set.first().unit, self.unit_g)

    def test_update_recipe(self):
        # Try to update existing recipe as the author
        new_ing = Ingredient.objects.create(name="Milk")
        new_unit = Unit.objects.create(name="Liter", abbreviation="l")
        new_title = "Coffee"
        new_description = "Yummy"
        new_notes = "Not so yummy"
        new_instructions = ["Do", "Blend"]
        url = f"/api/kitchen/recipes/{self.recipe.uid}"
        payload = {
            "title": new_title,
            "description": new_description,
            "image": None,
            "notes": new_notes,
            "instructions": new_instructions,
            "ingredients": [
                {
                    "ingredient_uid": str(new_ing.uid),
                    "unit_uid": str(new_unit.uid),
                    "quantity": 100,
                }
            ],
        }

        resp = self.client.patch(
            url,
            data=payload,
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )
        data = resp.json()

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(data["title"], new_title)
        self.assertEqual(data["description"], new_description)
        self.assertEqual(data["notes"], new_notes)
        self.assertEqual(data["instructions"], new_instructions)
        self.assertEqual(len(data["ingredients"]), 1)
        self.assertEqual(data["ingredients"][0]["quantity"], 100)
        self.assertEqual(data["ingredients"][0]["ingredient"]["uid"], str(new_ing.uid))
        self.assertEqual(data["ingredients"][0]["unit"]["uid"], str(new_unit.uid))

    def test_update_recipe_forbidden_for_non_author(self):
        # Try to update existing recipe as a different user
        url = f"/api/kitchen/recipes/{self.recipe.uid}"
        payload = {
            "title": "New Name",  # schema requires this field
            "description": "Hacked",
            "image": None,
            "notes": None,
            "instructions": ["Do"],
            "ingredients": [],  # keep empty to avoid ingredient changes
        }
        resp = self.client.patch(
            url,
            data=payload,
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp.json().get("error"), "Forbidden")
