from django.db import models

from tools.app_models import TimeTrackedModel

# Create your models here.


class AttentionMarket(TimeTrackedModel):
    slug = models.CharField(max_length=255, unique=True)
    address = models.CharField(max_length=255)
