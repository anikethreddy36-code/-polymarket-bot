import os
import requests

from py_clob_client.client import ClobClient
from py_clob_client.clob_types import MarketOrderArgs, OrderType
from py_clob_client.order_builder.constants import BUY

HOST = "https://clob.polymarket.com"
CHAIN_ID = 137

MAX_TRADE_USDC = 2.00
MIN_PRICE = 0.65
MAX_PRICE = 0.80


def main():
    private_key = os.environ["POLYMARKET_PRIVATE_KEY"]
    funder = os.environ["POLYMARKET_DEPOSIT_WALLET"]

    # Deposit-wallet setup
    client = ClobClient(
        HOST,
        key=private_key,
        chain_id=CHAIN_ID,
        signature_type=3,
        funder=funder,
    )

    # Derive existing API credentials
    client.set_api_creds(client.create_or_derive_api_creds())

    # Get active markets
    response = requests.get(
        "https://gamma-api.polymarket.com/markets",
        params={
            "active": "true",
            "closed": "false",
            "limit": 100,
        },
        timeout=20,
    )
    response.raise_for_status()

    markets = response.json()

    selected = None

    for market in markets:
        if not market.get("active"):
            continue
        if market.get("closed"):
            continue

        tokens = market.get("tokens") or []

        for token in tokens:
            if str(token.get("outcome", "")).upper() != "YES":
                continue

            token_id = token.get("token_id")
            if not token_id:
                continue

            try:
                book = client.get_order_book(token_id)

                if not book.bids:
                    continue

                best_bid = float(book.bids[0].price)

                if MIN_PRICE <= best_bid <= MAX_PRICE:
                    selected = (
                        market.get("question", "Unknown market"),
                        token_id,
                        best_bid,
                    )
                    break

            except Exception as e:
                print("Market skipped:", e)

        if selected:
            break

    if selected is None:
        print("No qualifying trade found.")
        return

    question, token_id, price = selected

    print("LIVE TRADE SELECTED")
    print("Market:", question)
    print("YES price:", price)
    print("Maximum spend:", MAX_TRADE_USDC)

    # Real-money market BUY.
    order = MarketOrderArgs(
        token_id=token_id,
        amount=MAX_TRADE_USDC,
        side=BUY,
        order_type=OrderType.FAK,
    )

    signed = client.create_market_order(order)
    result = client.post_order(signed, OrderType.FAK)

    print("ORDER RESULT:")
    print(result)


if __name__ == "__main__":
    main()
