# yourapp/management/commands/update_asset_prices.py
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
import requests
import time
import math

from trades.models import Asset  # replace with your app name

API_URL = "https://api.twelvedata.com/quote"  # batch quote endpoint
DEFAULT_BATCH_SIZE = 50
DEFAULT_DELAY_SECONDS = 8.0  # TwelveData basic: 8 calls/min => ~7.5s, use 8s to be safe


class Command(BaseCommand):
    help = "Fetch and update asset prices from TwelveData (batching & rate-limit aware)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--symbols",
            type=str,
            help="Comma-separated symbols to update (overrides DB). Example: BTC/USD,AAPL,EUR/USD",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=DEFAULT_BATCH_SIZE,
            help=f"Number of symbols per API request (default: {DEFAULT_BATCH_SIZE})",
        )
        parser.add_argument(
            "--delay",
            type=float,
            default=DEFAULT_DELAY_SECONDS,
            help=f"Seconds to pause between batch requests (default: {DEFAULT_DELAY_SECONDS})",
        )
        parser.add_argument(
            "--seed",
            action="store_true",
            help="Seed DB with a small list of assets (useful first run)",
        )

    def handle(self, *args, **options):
        # optional seeding
        if options["seed"]:
            self.seed_assets()
            return

        if options.get("symbols"):
            symbols = [s.strip() for s in options["symbols"].split(",") if s.strip()]
        else:
            symbols = list(Asset.objects.values_list("symbol", flat=True))

        if not symbols:
            self.stdout.write(self.style.WARNING("No symbols to update. Add assets to the DB or pass --symbols."))
            return

        batch_size = max(1, int(options.get("batch_size", DEFAULT_BATCH_SIZE)))
        delay = float(options.get("delay", DEFAULT_DELAY_SECONDS))

        # chunk symbols into batches
        total = len(symbols)
        batches = math.ceil(total / batch_size)
        self.stdout.write(f"Updating {total} symbols in {batches} batch(es) (batch_size={batch_size}, delay={delay}s)")

        for i in range(0, total, batch_size):
            batch = symbols[i : i + batch_size]
            symbol_str = ",".join(batch)

            params = {"symbol": symbol_str, "apikey": settings.TWELVE_DATA_API_KEY}

            try:
                resp = requests.get(API_URL, params=params, timeout=15)
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"API request failed for batch {batch}: {e}"))
                # be conservative: wait before next attempt
                time.sleep(delay)
                continue

            # The API can return a mapping keyed by symbol for batch queries.
            # Handle both dict-per-symbol and single-symbol responses.
            for sym in batch:
                # try exact key, then try variants
                entry = data.get(sym) or data.get(sym.upper()) or data.get(sym.replace("/", "")) or data.get(sym.replace("/", "").upper())
                if not entry:
                    # Case: some APIs return a single dict (for single-symbol call) or error field
                    # Try if top-level 'price' exists (single-symbol response)
                    if isinstance(data, dict) and ("price" in data or "close" in data):
                        entry = data
                if not entry or not isinstance(entry, dict):
                    self.stderr.write(self.style.WARNING(f"No data for symbol {sym}. Full response: {data}"))
                    continue

                # Prefer close -> price -> last
                price_str = entry.get("close") or entry.get("price") or entry.get("last") or entry.get("value")
                try:
                    if price_str is None:
                        raise ValueError("No price field found in API response for symbol")
                    price = Decimal(str(price_str))
                except Exception as e:
                    self.stderr.write(self.style.ERROR(f"Failed to parse price for {sym}: {e} -- entry: {entry}"))
                    continue

                # Update or create the Asset row
                # If the asset row already exists, update current_price and last_updated.
                # If not, create a new Asset with empty name and default asset_type if needed.
                obj, created = Asset.objects.update_or_create(
                    symbol=sym,
                    defaults={
                        "current_price": price,
                        "last_updated": timezone.now(),
                    },
                )
                verb = "Created" if created else "Updated"
                self.stdout.write(self.style.SUCCESS(f"{verb} Asset {sym}: {price}"))

            # throttle between batches (avoid sleeping after final batch)
            if i + batch_size < total:
                time.sleep(delay)

        self.stdout.write(self.style.SUCCESS("Asset price update completed."))

    def seed_assets(self):
        """Simple bootstrap list — change symbols/names/asset_type to match your needs."""
        seed_list = [
            {"symbol": "BTC/USD", "name": "Bitcoin / USD", "asset_type": "crypto"},
            {"symbol": "ETH/USD", "name": "Ethereum / USD", "asset_type": "crypto"},
            {"symbol": "AAPL", "name": "Apple Inc.", "asset_type": "stock"},
            {"symbol": "EUR/USD", "name": "EUR / USD", "asset_type": "forex"},
        ]
        for item in seed_list:
            obj, created = Asset.objects.update_or_create(
                symbol=item["symbol"],
                defaults={
                    "name": item["name"],
                    "current_price": Decimal("0.0"),
                    "last_updated": timezone.now(),
                    "asset_type": item.get("asset_type", "crypto"),  # requires field in model
                },
            )
            self.stdout.write(self.style.SUCCESS(f"{'Created' if created else 'Updated'} {obj.symbol}"))
        self.stdout.write(self.style.SUCCESS("Seeding done. Edit asset list in admin or add more via --symbols."))
