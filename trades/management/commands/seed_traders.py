# app/management/commands/seed_traders.py
from django.core.management.base import BaseCommand
from trades.models import Trader

class Command(BaseCommand):
    help = "Seeds the Trader table with initial data"

    def handle(self, *args, **kwargs):
        traders = [
            {"stars": 5, "name": "Alpha Trader", "returns": 67, "win_rate": 89, "copiers": 457},
            {"stars": 4, "name": "Beta Shark", "returns": 52, "win_rate": 83, "copiers": 312},
            {"stars": 5, "name": "CryptoKing", "returns": 75, "win_rate": 91, "copiers": 624},
            {"stars": 3, "name": "SwingBoss", "returns": 43, "win_rate": 78, "copiers": 198},
            {"stars": 4, "name": "SniperFX", "returns": 61, "win_rate": 85, "copiers": 351},
            {"stars": 5, "name": "Elite Trader", "returns": 88, "win_rate": 93, "copiers": 734},
            {"stars": 2, "name": "RiskyPip", "returns": 29, "win_rate": 60, "copiers": 97},
            {"stars": 3, "name": "ForexFalcon", "returns": 49, "win_rate": 76, "copiers": 214},
            {"stars": 4, "name": "SteadyProfit", "returns": 58, "win_rate": 82, "copiers": 289},
        ]

        for trader in traders:
            Trader.objects.get_or_create(**trader)

        self.stdout.write(self.style.SUCCESS("✅ Traders seeded successfully!"))
