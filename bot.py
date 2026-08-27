import os
from polymarket import SecureClient

MAX_TRADE = 2.00
MIN_PRICE = 0.55
MAX_PRICE = 0.80


def main():
    private_key = os.environ["POLYMARKET_PRIVATE_KEY"]
    wallet = os.environ["POLYMARKET_DEPOSIT_WALLET"]

    client = SecureClient.create(
        private_key=private_key,
        wallet=wallet,
    )

    with client:
        markets = client.list_markets(
            closed=False,
            page_size=100,
        )

        selected = None

        for market in markets.iter_items():
            if not market.state.enable_order_book:
                continue

            if not market.state.accepting_orders:
                continue

            token_id = market.outcomes.yes.token_id
            if not token_id:
                continue

            minimum = market.trading.minimum_order_size
            if minimum is None or minimum > MAX_TRADE:
                continue

            try:
                price = client.estimate_market_price(
                    token_id=token_id,
                    side="BUY",
                    amount=MAX_TRADE,
                    order_type="FAK",
                )
            except Exception:
                continue

            if MIN_PRICE <= price <= MAX_PRICE:
                selected = (market, token_id, price)
                break

        if selected is None:
            print("No qualifying trade found.")
            return

        market, token_id, price = selected

        print("LIVE TRADE SELECTED")
        print("Market:", market.question or market.slug or market.id)
        print("Price:", price)
        print("Amount:", MAX_TRADE)

        # LIVE REAL-MONEY ORDER
        result = client.place_market_order(
            token_id=token_id,
            side="BUY",
            amount=MAX_TRADE,
            order_type="FAK",
        )

        print("ORDER RESULT:")
        print(result)


if __name__ == "__main__":
    main()
