from django.db import models


class UUIDv7(models.Func):
    function = "uuidv7"
    output_field = models.UUIDField()


class UIDed(models.Model):
    class Meta:
        abstract = True

    uid = models.UUIDField(primary_key=True, db_default=UUIDv7(), editable=False)


class Dated(models.Model):
    class Meta:
        abstract = True

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True)


class Common(UIDed, Dated):
    class Meta:
        abstract = True
