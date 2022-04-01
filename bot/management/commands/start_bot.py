
from django.core.management.base import BaseCommand
from bot.bot_service import BotService


class Command(BaseCommand):
    help = 'Start TG bot'

    def handle(self, *args, **kwargs):
        bot = BotService()
        bot.main()
