
from django.core.management.base import BaseCommand
from bot.bot_service import BotService, BotServiceV2, BotServiceV3


class Command(BaseCommand):
    help = 'Start TG bot'

    def handle(self, *args, **kwargs):
        bot = BotServiceV3()
        bot.main()
