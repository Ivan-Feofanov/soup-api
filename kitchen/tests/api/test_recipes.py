import pytest
from ninja_extra import status

from kitchen.models import Ingredient, Unit, Recipe


@pytest.mark.django_db
def test_list_recipes_private(authenticated_client, recipe, user):
    resp = authenticated_client.get("/api/kitchen/recipes/")
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    first = data[0]

    assert isinstance(data, list)
    assert len(data) >= 1
    assert first["title"] == "Bread"
    # Author block
    assert "author" in first
    assert first["author"]["username"] == user.username
    assert first["author"]["handler"] == user.handler


@pytest.mark.django_db
def test_list_recipes_unauthenticated(client, recipe, user):
    resp = client.get("/api/kitchen/recipes/")
    assert resp.status_code == status.HTTP_200_OK

    assert resp.json() == []


@pytest.mark.django_db
def test_list_recipes_unauthenticated_public(client, recipe, user):
    recipe.visibility = "PUBLIC"
    recipe.save()

    resp = client.get("/api/kitchen/recipes/")
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()

    assert len(data) == 1
    assert data[0]["uid"] == str(recipe.uid)


@pytest.mark.django_db
def test_list_recipes_public_and_private(authenticated_client, recipe, other_user):
    public_recipe = other_user.recipe_set.create(
        author=other_user,
        title="Other's recipe",
        description="Other's description",
        visibility=Recipe.Visibility.PUBLIC,
    )
    other_user.recipe_set.create(
        author=other_user,
        title="Other's recipe",
        description="Other's description",
        visibility=Recipe.Visibility.PRIVATE,
    )

    resp = authenticated_client.get("/api/kitchen/recipes/")
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()

    assert len(data) == 2
    assert {x["uid"] for x in data} == {str(recipe.uid), str(public_recipe.uid)}


@pytest.mark.django_db
def test_get_recipe(
    authenticated_client, recipe, user, ing_flour, ing_water, unit_g, unit_ml
):
    resp = authenticated_client.get(f"/api/kitchen/recipes/{recipe.uid}")
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    db_recipe = Recipe.objects.get(uid=recipe.uid)

    assert data["uid"] == str(db_recipe.uid)
    assert data["title"] == db_recipe.title
    assert data["description"] == db_recipe.description
    assert data["instructions"] == [
        {
            "uid": str(x.uid),
            "step": x.step,
            "description": x.description,
            "timer": x.timer,
        }
        for x in db_recipe.instructions.all()
    ]
    assert data["notes"] == db_recipe.notes
    assert data["image"] == db_recipe.image
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
    assert data["author"]["username"] == user.username
    assert data["author"]["handler"] == user.handler


@pytest.mark.django_db
def test_get_public_recipe(client, recipe, user, ing_flour, ing_water, unit_g, unit_ml):
    recipe.visibility = "PUBLIC"
    recipe.save()

    resp = client.get(f"/api/kitchen/recipes/{recipe.uid}")
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()

    assert data["uid"] == str(recipe.uid)


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

    # JWT returns 401 for unauthenticated requests
    assert r.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_create_recipe(faker, authenticated_client, ing_flour, unit_g, user):
    new_recipe_data = {
        "title": faker.sentence(),
        "description": faker.text(),
        "image": faker.image_url(),
        "notes": faker.text(),
    }
    url = "/api/kitchen/recipes/"
    instr = {
        "step": 1,
        "description": faker.sentence(),
        "timer": 10,
    }
    payload = {
        "title": new_recipe_data["title"],
        "description": new_recipe_data["description"],
        "image": new_recipe_data["image"],
        "notes": new_recipe_data["notes"],
        "instructions": [instr],
        "ingredients": [
            {
                "ingredient_uid": str(ing_flour.uid),
                "unit_uid": str(unit_g.uid),
                "quantity": 100,
            }
        ],
    }

    response = authenticated_client.post(
        url,
        data=payload,
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    new_recipe = Recipe.objects.get(title=new_recipe_data["title"])

    assert data["title"] == new_recipe_data["title"]
    assert data["description"] == new_recipe_data["description"]
    assert data["image"] == new_recipe_data["image"]
    assert data["notes"] == new_recipe_data["notes"]
    assert len(data["instructions"]) == 1
    assert data["instructions"][0]["step"] == instr["step"]
    assert data["instructions"][0]["description"] == instr["description"]
    assert data["instructions"][0]["timer"] == instr["timer"]
    assert len(data["ingredients"]) == 1
    # DB side checks
    assert new_recipe.recipeingredient_set.count() == 1
    assert new_recipe.recipeingredient_set.first().ingredient == ing_flour
    assert new_recipe.recipeingredient_set.first().unit == unit_g


@pytest.mark.django_db
def test_update_recipe(faker, authenticated_client, recipe):
    # Try to update existing recipe as the author
    new_ing = Ingredient.objects.create(name="Milk")
    new_unit = Unit.objects.create(name="Liter", abbreviation="l")
    new_title = faker.sentence()
    new_description = faker.text()
    new_notes = faker.text()
    new_image = faker.image_url()
    new_instructions = [
        {
            "step": 1,
            "description": "Mix all ingredients",
            "timer": 10,
        }
    ]
    url = f"/api/kitchen/recipes/{recipe.uid}"
    payload = {
        "title": new_title,
        "description": new_description,
        "image": new_image,
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

    resp = authenticated_client.patch(
        url,
        data=payload,
        content_type="application/json",
    )
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()

    assert data["title"] == new_title
    assert data["description"] == new_description
    assert data["notes"] == new_notes
    assert data["image"] == new_image
    assert len(data["instructions"]) == 1
    assert data["instructions"][0]["step"] == new_instructions[0]["step"]
    assert data["instructions"][0]["description"] == new_instructions[0]["description"]
    assert data["instructions"][0]["timer"] == new_instructions[0]["timer"]
    assert len(data["ingredients"]) == 1
    assert data["ingredients"][0]["quantity"] == 100
    assert data["ingredients"][0]["ingredient"]["uid"] == str(new_ing.uid)
    assert data["ingredients"][0]["unit"]["uid"] == str(new_unit.uid)


@pytest.mark.django_db
def test_update_recipe_forbidden_for_non_author(
    client, get_authenticated_client, other_user, recipe
):
    # Try to update existing recipe as a different user
    url = f"/api/kitchen/recipes/{recipe.uid}"
    payload = {
        "title": "New Name",  # schema requires this field
        "description": "Hacked",
        "image": None,
        "notes": None,
        "instructions": [],
        "ingredients": [],  # keep empty to avoid ingredient changes
    }
    other_client = get_authenticated_client(other_user)

    resp = other_client.patch(
        url,
        data=payload,
        content_type="application/json",
    )

    assert resp.status_code == status.HTTP_403_FORBIDDEN
    assert (
        resp.json().get("detail")
        == "You do not have permission to perform this action."
    )


@pytest.mark.django_db
def test_delete_recipe(authenticated_client, recipe):
    url = f"/api/kitchen/recipes/{recipe.uid}"
    resp = authenticated_client.delete(
        url,
        content_type="application/json",
    )

    assert resp.status_code == status.HTTP_204_NO_CONTENT
    assert not Recipe.objects.filter(uid=recipe.uid).exists()


@pytest.mark.django_db
def test_delete_recipe_forbidden_for_non_author(
    client, get_authenticated_client, other_user, recipe
):
    url = f"/api/kitchen/recipes/{recipe.uid}"
    other_client = get_authenticated_client(other_user)

    resp = other_client.delete(
        url,
        content_type="application/json",
    )
    assert resp.status_code == status.HTTP_403_FORBIDDEN
