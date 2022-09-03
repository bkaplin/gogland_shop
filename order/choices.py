from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class PayType(models.TextChoices):
   CASH = 'CASH', _(settings.CASH_ICON)
   CARD = 'CARD', _(settings.CARD_ICON)
