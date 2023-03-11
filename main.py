from kuCoinApi import KucoinWebsocket, get_coins, stableG
import time
from threading import Thread


def calc(usdt_ada, ada_usdc, usdt_usdc):
    amount_ada = 1 / float(usdt_ada['asks'])
    amount_usdc = amount_ada * float(ada_usdc['bids'])
    amount_usdt = amount_usdc * (1 / float(usdt_usdc['bids']))
    profit = amount_usdt - 1

    return profit * 100


def main():
    kucoin_ws = KucoinWebsocket()
    thread = Thread(target=kucoin_ws.start)
    thread.start()
    time.sleep(30)
    coins = get_coins()
    spot = kucoin_ws.priceSpot
    stable = kucoin_ws.priceStable

    while True:
        for coin in coins:
            profit = calc(spot[coin][stableG[0]], spot[coin][stableG[1]], stable)
            if profit > 0.3:
                print(f"{coin}: {round(profit, 3)}")


main()
