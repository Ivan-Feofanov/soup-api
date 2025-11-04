import pytest

from kitchen.models import Recipe


@pytest.mark.django_db
def test_recipe_slug_is_set_on_save(faker, user):
    recipe = Recipe(title=faker.sentence(), author=user)

    recipe.save()

    assert recipe.slug is not None


@pytest.mark.django_db
def test_recipe_slug_is_unique(faker, user):
    title = faker.sentence()
    recipe1 = Recipe(title=title, author=user)
    recipe2 = Recipe(title=title, author=user)

    recipe1.save()
    recipe2.save()

    assert recipe1.slug != recipe2.slug
