import requests
import websocket
import json
import time

stableG = ['USDT', 'USDC']


def get_all_pair():
    url = "https://api.kucoin.com/api/v2/symbols"
    response = requests.get(url)

    if response.status_code == 200:
        symbols_info = response.json()
        coins = set()

        for symbol in symbols_info["data"]:
            if symbol["quoteCurrency"] in stableG:
                coins.add(symbol["baseCurrency"])

        common_coins = set.intersection(*[
            set(symbol_info["baseCurrency"]
                for symbol_info in symbols_info["data"]
                if symbol_info["quoteCurrency"] == s) for s in stableG
        ])
        coins = list(coins.intersection(common_coins))
        with open(f"json/coinKucoin.json", "w") as f:
            json.dump(coins, f, indent=4)


get_all_pair()


def get_coins():

    with open('./json/coinKucoin.json') as jsonFile:
        dictListCoin = json.load(jsonFile)
        return dictListCoin


class KucoinWebsocket:

    def __init__(self):
        self.temp_token = None
        self.url = None
        self.ws = None
        self.is_connected = False

        self.priceSpot = {}
        dictLictCoin = get_coins()
        for symbol in dictLictCoin:
            self.priceSpot[symbol] = {}
            for market in stableG:
                self.priceSpot[symbol][market] = {"asks": "", "bids": ""}
        self.priceStable = {}
        self.pairs = [coin + f"-{stableG[1]}" for coin in dictLictCoin
                      ] + [coin + f"-{stableG[0]}" for coin in dictLictCoin]
        self.pairs += [f"{stableG[0]}-{stableG[1]}"]

    def get_temp_token(self):
        url = 'https://openapi-v2.kucoin.com/api/v1/bullet-public'
        response = requests.post(url)
        if response.status_code == 200:
            data = response.json()['data']
            self.temp_token = data['token']
            self.url = data['instanceServers'][0]['endpoint']
        return response.status_code

    def connect(self):
        self.ws = websocket.WebSocketApp(self.url + "?token=" +
                                         self.temp_token,
                                         on_open=self.on_open,
                                         on_message=self.on_message,
                                         on_error=self.on_error,
                                         on_close=self.on_close)

        self.ws.run_forever(ping_interval=18, ping_timeout=10)

    def on_open(self, ws):
        print("WebSocket connection is open!")
        self.subscribe('/spotMarket/level2Depth5:' + ','.join(self.pairs))
        self.is_connected = True

    def on_message(self, ws, message):
        msg = json.loads(message)
        data = msg.get('data')
        if data is not None:
            stable = msg['topic'].split("-")[1]
            coin = msg['topic'].split(":")[1].split("-")[0]
            if coin == stableG[0]:
                self.priceStable['asks'] = data['asks'][0][0]
                self.priceStable['bids'] = data['bids'][0][0]
            else:
                self.priceSpot[coin][stable]['asks'] = data['asks'][2][0]
                self.priceSpot[coin][stable]['bids'] = data['bids'][2][0]

    def on_error(self, ws, error):
        print(f"WebSocket error: {error}")

    def on_close(self, ws):
        print("WebSocket connection closed.")
        self.is_connected = False
        raise Exception("WebSocket connection closed.", 23)

    def subscribe(self, topic):
        subscribe_message = {
            "id": str(int(time.time() * 1000)),
            "type": "subscribe",
            "topic": topic,
            "privateChannel": False,
            "response": True
        }
        self.ws.send(json.dumps(subscribe_message))

    def start(self):
        if (self.get_temp_token() != 200):
            print("Ошибка подключения.")
            return
        self.connect()
