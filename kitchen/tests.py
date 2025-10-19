import pytest
from django.test import Client
from ninja_jwt.tokens import RefreshToken

from users.models import CustomUser
from kitchen.models import Ingredient, Unit, Recipe, RecipeIngredient


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def password():
    return "pass1234!"


@pytest.fixture
def user(password):
    return CustomUser.objects.create_user(
        email="chef@example.com",
        password=password,
        username="chef",
        handler="chef-handler",
    )


@pytest.fixture
def other_user(password):
    return CustomUser.objects.create_user(
        email="intruder@example.com", password=password
    )


@pytest.fixture
def token(get_token, user):
    return get_token(user)


@pytest.fixture
def get_token(client):
    def _get_token(user: CustomUser) -> str:
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)

    return _get_token


@pytest.fixture
def unit_g():
    return Unit.objects.create(name="Gram", abbreviation="g")


@pytest.fixture
def unit_ml():
    return Unit.objects.create(name="Milliliter", abbreviation="ml")


@pytest.fixture
def ing_flour():
    return Ingredient.objects.create(name="Flour")


@pytest.fixture
def ing_water():
    return Ingredient.objects.create(name="Water")


@pytest.fixture
def recipe(user, ing_flour, ing_water, unit_g, unit_ml):
    recipe = Recipe.objects.create(
        author=user,
        title="Bread",
        description="Simple bread",
        instructions=["Mix", "Bake"],
    )
    RecipeIngredient.objects.create(
        recipe=recipe,
        ingredient=ing_flour,
        unit=unit_g,
        quantity=500,
    )
    RecipeIngredient.objects.create(
        recipe=recipe,
        ingredient=ing_water,
        unit=unit_ml,
        quantity=300,
    )
    return recipe


@pytest.mark.django_db
def test_list_recipes(client, recipe, user):
    resp = client.get("/api/kitchen/recipes/")
    data = resp.json()
    first = data[0]
    ing_names = sorted(i["ingredient"]["name"] for i in first["ingredients"])
    units = sorted(i["unit"]["abbreviation"] for i in first["ingredients"])

    assert resp.status_code == 200
    assert isinstance(data, list)
    assert len(data) >= 1
    assert first["title"] == "Bread"
    # Author block
    assert "author" in first
    assert first["author"]["email"] == user.email
    # Ingredients resolved with unit abbreviation and quantity
    assert "ingredients" in first
    assert ing_names == ["Flour", "Water"]
    assert sorted(units) == ["g", "ml"]


@pytest.mark.django_db
def test_get_recipe(client, recipe, user, ing_flour, ing_water, unit_g, unit_ml):
    resp = client.get(f"/api/kitchen/recipes/{recipe.uid}")
    data = resp.json()

    assert resp.status_code == 200
    assert data["uid"] == str(recipe.uid)
    assert data["title"] == "Bread"
    assert data["description"] == "Simple bread"
    assert data["instructions"] == ["Mix", "Bake"]
    assert data["notes"] is None
    assert data["image"] is None
    # Ingredients resolved with unit abbreviation and quantity
    assert len(data["ingredients"]) == 2
    assert data["ingredients"][0]["quantity"] == 500
    assert data["ingredients"][0]["ingredient"]["uid"] == str(ing_flour.uid)
    assert data["ingredients"][0]["ingredient"]["name"] == "Flour"
    assert data["ingredients"][0]["unit"]["uid"] == str(unit_g.uid)
    assert data["ingredients"][0]["unit"]["abbreviation"] == "g"
    assert data["ingredients"][0]["unit"]["name"] == "Gram"
    assert data["ingredients"][1]["quantity"] == 300
    assert data["ingredients"][1]["ingredient"]["uid"] == str(ing_water.uid)
    assert data["ingredients"][1]["ingredient"]["name"] == "Water"
    assert data["ingredients"][1]["unit"]["uid"] == str(unit_ml.uid)
    assert data["ingredients"][1]["unit"]["abbreviation"] == "ml"
    assert data["ingredients"][1]["unit"]["name"] == "Milliliter"
    # Author block
    assert "author" in data
    assert data["author"]["email"] == user.email


@pytest.mark.django_db
def test_list_ingredients(client, ing_flour, ing_water):
    resp = client.get("/api/kitchen/ingredients/")
    data = resp.json()
    names = sorted(d["name"] for d in data)

    assert resp.status_code == 200
    assert {"Flour", "Water"}.issubset(set(names))


@pytest.mark.django_db
def test_list_units(client, unit_g, unit_ml):
    resp = client.get("/api/kitchen/units/")
    data = resp.json()
    abbrevs = [d["abbreviation"] for d in data]

    assert resp.status_code == 200
    assert "g" in abbrevs
    assert "ml" in abbrevs


@pytest.mark.django_db
def test_create_ingredient(client, token):
    url = "/api/kitchen/ingredients/"
    payload = {"name": "Sugar"}

    resp = client.post(
        url,
        data=payload,
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )
    data = resp.json()

    assert resp.status_code == 200
    assert data["name"] == "Sugar"
    assert Ingredient.objects.filter(name="Sugar").exists()


@pytest.mark.django_db
def test_create_ingredient_idempotent_by_name(client, token):
    url = "/api/kitchen/ingredients/"
    payload = {"name": "Sugar"}
    r1 = client.post(
        url,
        data=payload,
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )
    first_uid = r1.json()["uid"]

    # Posting same name should return existing ingredient (same uid)
    r2 = client.post(
        url,
        data=payload,
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )

    assert r2.status_code == 200
    assert r2.json()["uid"] == first_uid
    assert Ingredient.objects.filter(name="Sugar").count() == 1


@pytest.mark.django_db
def test_create_recipe_non_auth(client, ing_flour):
    url = "/api/kitchen/recipes/"
    payload = {
        "title": "Pancakes",
        "description": "Yummy",
        "image": None,
        "notes": None,
        "instructions": ["Mix", "Fry"],
        "ingredients": [
            {
                "ingredient_uid": str(ing_flour.uid),
            }
        ],
    }

    r = client.post(url, data=payload, content_type="application/json")

    assert r.status_code == 401


@pytest.mark.django_db
def test_create_recipe(client, token, ing_flour, unit_g, user):
    url = "/api/kitchen/recipes/"
    payload = {
        "title": "Pancakes",
        "description": "Yummy",
        "image": None,
        "notes": None,
        "instructions": ["Mix", "Fry"],
        "ingredients": [
            {
                "ingredient_uid": str(ing_flour.uid),
                "unit_uid": str(unit_g.uid),
                "quantity": 100,
            }
        ],
    }

    response = client.post(
        url,
        data=payload,
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )
    data = response.json()
    new_recipe = Recipe.objects.get(title="Pancakes")

    assert response.status_code == 200, response.content
    assert data["title"] == "Pancakes"
    assert len(data["ingredients"]) == 1
    # DB side checks
    assert Recipe.objects.filter(title="Pancakes", author=user).exists()
    assert new_recipe.recipeingredient_set.count() == 1
    assert new_recipe.recipeingredient_set.first().ingredient == ing_flour
    assert new_recipe.recipeingredient_set.first().unit == unit_g


@pytest.mark.django_db
def test_update_recipe(client, token, recipe):
    # Try to update existing recipe as the author
    new_ing = Ingredient.objects.create(name="Milk")
    new_unit = Unit.objects.create(name="Liter", abbreviation="l")
    new_title = "Coffee"
    new_description = "Yummy"
    new_notes = "Not so yummy"
    new_instructions = ["Do", "Blend"]
    url = f"/api/kitchen/recipes/{recipe.uid}"
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

    resp = client.patch(
        url,
        data=payload,
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )
    data = resp.json()

    assert resp.status_code == 200
    assert data["title"] == new_title
    assert data["description"] == new_description
    assert data["notes"] == new_notes
    assert data["instructions"] == new_instructions
    assert len(data["ingredients"]) == 1
    assert data["ingredients"][0]["quantity"] == 100
    assert data["ingredients"][0]["ingredient"]["uid"] == str(new_ing.uid)
    assert data["ingredients"][0]["unit"]["uid"] == str(new_unit.uid)


@pytest.mark.django_db
def test_update_recipe_forbidden_for_non_author(client, get_token, other_user, recipe):
    # Try to update existing recipe as a different user
    url = f"/api/kitchen/recipes/{recipe.uid}"
    payload = {
        "title": "New Name",  # schema requires this field
        "description": "Hacked",
        "image": None,
        "notes": None,
        "instructions": ["Do"],
        "ingredients": [],  # keep empty to avoid ingredient changes
    }
    token = get_token(other_user)

    resp = client.patch(
        url,
        data=payload,
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )

    assert resp.status_code == 403
    assert (
        resp.json().get("detail")
        == "You do not have permission to perform this action."
    )
