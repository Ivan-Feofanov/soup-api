import factory
from factory.django import DjangoModelFactory

from users.models import CustomUser


class CustomUserFactory(DjangoModelFactory):
    class Meta:
        model = CustomUser
        django_get_or_create = ["email"]

    email = factory.Faker("email")
    username = factory.Faker("name")
    handler = factory.Faker("word")
    password = factory.Faker("password")
