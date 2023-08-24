import datetime
import json
import ccxt.async_support as ccxt_async
import ccxt
import asyncio

class ConfigManager:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config_data = self.load_config()

    def load_config(self) -> dict:
        """Зчитує конфігураційний файл."""
        with open(self.config_path, 'r') as file:
            return json.load(file)

    def get_param(self, param_name: str) -> any:
        """Повертає значення параметра."""
        return self.config_data.get(param_name, None)

    def get_exchange_credentials(self, exchange_name: str) -> dict:
        """Повертає API ключ та секрет для вказаної біржі."""
        return self.config_data.get("exchanges", {}).get(exchange_name, {})

    def get_risk_management(self) -> dict:
        """Повертає параметри управління ризиками."""
        return self.config_data.get("risk_management", {})

    def get_backup_params(self) -> dict:
        """Повертає параметри для резервного копіювання."""
        return self.config_data.get("backup", {})

    def get_logging_params(self) -> dict:
        """Повертає параметри логування."""
        return self.config_data.get("logging", {})

    def get_notification_params(self) -> dict:
        """Повертає параметри для сповіщень."""
        return self.config_data.get("notifications", {})

    def get_selected_assets(self) -> list:
        """Повертає список вибраних валютних пар."""
        return self.config_data.get("currency_pairs", {}).get("selected_assets", [])

    def get_transaction_fee(self) -> float:
        """Повертає комісію за транзакцію."""
        return self.config_data.get("transaction", {}).get("fee", 0.0)
    
    def get_risk_parameters(self):
        """Повертає ризикові параметри з конфігураційного файлу."""
        return self.config_data.get("risk_parameters", {})
    
    def get_currency_pairs(self):
        return self.config['currency_pairs']['selected_assets']
    
    def get_polling_interval(self):
        return self.config['polling_interval']

class ExchangeAPI:
    def __init__(self, config_manager: ConfigManager, exchange_name: str):
        self.config_manager = config_manager
        credentials = self.config_manager.get_exchange_credentials(exchange_name)
        self.exchange = getattr(ccxt_async, exchange_name)({
            'apiKey': credentials["api_key"],
            'secret': credentials["api_secret"],
        })

    async def get_data(self, symbol: str, timeframe: str, since=None, limit=None):
        """Отримує історичні дані для вказаної валютної пари."""
        return await self.exchange.fetch_ohlcv(symbol, timeframe, since, limit)

    async def rate_limit_handler(self):
        """Обробник обмежень на кількість запитів."""
        await self.exchange.throttle()

    async def get_balance(self):
        """Отримує баланс користувача на біржі."""
        return await self.exchange.fetch_balance()

    async def fetch_markets(self):
        """Отримує інформацію про всі доступні ринки на біржі."""
        return await self.exchange.fetch_markets()

    async def fetch_market(self, symbol: str):
        """Отримує інформацію про конкретний ринок."""
        return await self.exchange.fetch_market(symbol)

    async def fetch_ticker(self, symbol: str):
        """Отримує поточну ціну для вказаної валютної пари."""
        return await self.exchange.fetch_ticker(symbol)

    async def fetch_order_book(self, symbol: str, limit=None):
        """Отримує інформацію про замовлення для вказаної валютної пари."""
        return await self.exchange.fetch_order_book(symbol, limit)

    async def create_order(self, symbol: str, type: str, side: str, amount, price=None, params={}):
        """Створює замовлення на біржі."""
        return await self.exchange.create_order(symbol, type, side, amount, price, params)

    async def fetch_order(self, id: str, symbol: str):
        """Отримує інформацію про конкретне замовлення за його ID."""
        return await self.exchange.fetch_order(id, symbol)

    async def fetch_orders(self, symbol: str):
        """Отримує інформацію про всі замовлення користувача для вказаної валютної пари."""
        return await self.exchange.fetch_orders(symbol)

    async def cancel_order(self, id: str, symbol: str):
        """Відміняє замовлення за його ID."""
        return await self.exchange.cancel_order(id, symbol)

    async def fetch_symbols(self):
        """Отримує список всіх доступних обмінних пар на біржі."""
        return await self.exchange.fetch_symbols()

    async def fetch_market_details(self, symbol: str):
        """Отримує деталі ринку, такі як максимальний і мінімальний розмір замовлення, крок ціни тощо."""
        market_info = await self.exchange.fetch_market(symbol)
        return market_info['info']

    async def fetch_trades(self, symbol: str, since=None, limit=None):
        """Отримує інформацію про останні угоди для вказаної валютної пари."""
        return await self.exchange.fetch_trades(symbol, since, limit)

    async def fetch_deposits(self, currency=None, since=None, limit=None):
        """Отримує інформацію про депозити."""
        return await self.exchange.fetch_deposits(currency, since, limit)

    async def fetch_withdrawals(self, currency=None, since=None, limit=None):
        """Отримує інформацію про виведення коштів."""
        return await self.exchange.fetch_withdrawals(currency, since, limit)

    async def fetch_status(self):
        """Отримує інформацію про поточний статус біржі."""
        return await self.exchange.fetch_status()

    async def fetch_fees(self):
        """Отримує інформацію про комісії на біржі."""
        return await self.exchange.fetch_fees()

    async def fetch_currencies(self):
        """Отримує інформацію про всі валюти, доступні на біржі."""
        return await self.exchange.fetch_currencies()

    async def fetch_withdraw_limits(self, currency: str):
        """Отримує інформацію про обмеження на виведення коштів для конкретної валюти."""
        currencies_info = await self.exchange.fetch_currencies()
        return currencies_info[currency].get('limits', {}).get('withdraw')

    async def fetch_payment_methods(self):
        """Отримує інформацію про доступні методи внесення та виведення коштів."""
        return await self.exchange.fetch_payment_methods()

    async def fetch_open_orders(self, symbol: str):
        """Отримує інформацію про поточні замовлення для вказаної валютної пари."""
        return await self.exchange.fetch_open_orders(symbol)

    async def fetch_unfilled_orders(self, symbol: str):
        """Отримує інформацію про незавершені угоди для вказаної валютної пари."""
        all_orders = await self.exchange.fetch_open_orders(symbol)
        return [order for order in all_orders if order['remaining'] > 0]

    async def fetch_trading_limits(self, symbol: str):
        """Отримує інформацію про обмеження на торгівлю для вказаної валютної пари."""
        market_info = await self.exchange.fetch_market(symbol)
        return market_info.get('limits')

    async def has_symbol(self, symbol: str) -> bool:
        """Перевіряє, чи підтримує біржа конкретну валютну пару."""
        return symbol in await self.exchange.fetch_symbols()

    async def fetch_trading_fees(self):
        """Отримує інформацію про комісії за торгівлю."""
        return await self.exchange.fetch_trading_fees()

class ArbitrageAnalyzer:
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager

    def find_arbitrage_opportunity(self, exchange_data):
        """Знаходить можливості для арбітражу."""
        opportunities = []
        for symbol, data in exchange_data.items():
            buy_price = data['buy_price']
            sell_price = data['sell_price']
            if sell_price - buy_price > self.config_manager.get_min_price_difference():
                opportunities.append({
                    'symbol': symbol,
                    'buy_price': buy_price,
                    'sell_price': sell_price,
                    'profit': sell_price - buy_price
                })
        return opportunities

    def log_arbitrage_opportunity(self, opportunity):
        """Зберігає інформацію про арбітражну можливість."""
        with open("arbitrage_log.txt", "a") as file:
            file.write(f"Date: {datetime.now()}, Symbol: {opportunity['symbol']}, Buy Price: {opportunity['buy_price']}, Sell Price: {opportunity['sell_price']}, Profit: {opportunity['profit']}\n")

    def optimal_trade_volume(self, buy_order_book, sell_order_book):
        """Визначає оптимальний обсяг для арбітражу."""
        buy_volume = sum([order[1] for order in buy_order_book['bids']])
        sell_volume = sum([order[1] for order in sell_order_book['asks']])
        return min(buy_volume, sell_volume)

    def assess_risks(self, buy_price, sell_price, volume, execution_time):
        """Оцінює ризики, пов'язані з арбітражем."""
        risk_settings = self.config_manager.get_risk_parameters()
        price_difference = sell_price - buy_price
        risk_score = 0

        if price_difference < risk_settings["price_difference_threshold"]:
            risk_score += 1
        if volume > risk_settings["large_trade_volume"]:
            risk_score += 1
        if execution_time > risk_settings["long_execution_time"]:
            risk_score += 1

        return risk_score

    async def calculate_profit(self, buy_price: float, sell_price: float, amount: float):
        """Розраховує прибуток від арбітражу."""
        return (sell_price - buy_price) * amount

    async def consider_fees(self, buy_exchange, sell_exchange, symbol: str):
        """Враховує комісії при розрахунках."""
        buy_fee = await buy_exchange.fetch_trading_fees()[symbol]['maker']
        sell_fee = await sell_exchange.fetch_trading_fees()[symbol]['maker']
        return buy_fee, sell_fee

class TransactionManager:
    def __init__(self, exchange, config_manager: ConfigManager):
        self.exchange = exchange
        self.config_manager = config_manager

    async def create_buy_order(self, symbol, volume, price):
        """Створює замовлення на купівлю."""
        order = await self.exchange.create_limit_buy_order(symbol, volume, price)
        return order

    async def create_sell_order(self, symbol, volume, price):
        """Створює замовлення на продаж."""
        order = await self.exchange.create_limit_sell_order(symbol, volume, price)
        return order

    async def is_order_filled(self, order_id):
        """Перевіряє, чи було виконано замовлення."""
        order_status = await self.exchange.fetch_order_status(order_id)
        return order_status == 'closed'

    async def get_order_info(self, order_id):
        """Отримує інформацію про замовлення."""
        order_info = await self.exchange.fetch_order(order_id)
        return order_info

    def check_liquidity(self, symbol, volume):
        """Перевіряє, чи є достатньо ліквідності на біржі для виконання замовлення."""
        order_book = self.exchange.fetch_order_book(symbol)
        bids_volume = sum([order[1] for order in order_book['bids']])
        asks_volume = sum([order[1] for order in order_book['asks']])
        return bids_volume >= volume and asks_volume >= volume

class DataStorage:
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.data_file = "arbitrage_data.json"

    def save_data(self, data):
        """Зберігає дані в файл."""
        with open(self.data_file, "a") as file:
            json.dump(data, file)
            file.write("\n")

    def load_data(self):
        """Завантажує дані з файлу."""
        data = []
        with open(self.data_file, "r") as file:
            for line in file:
                data.append(json.loads(line))
        return data

    def log_arbitrage_transaction(self, transaction_data):
        """Зберігає інформацію про арбітражну транзакцію."""
        self.save_data(transaction_data)

    def get_transaction_history(self):
        """Отримує історію арбітражних транзакцій."""
        return self.load_data()

class CryptoArbitrage:
    def __init__(self, config_file):
        self.config_manager = ConfigManager(config_file)
        self.exchanges = {
            "bybit": ExchangeAPI(ccxt.bybit(), self.config_manager),
            "bitstamp": ExchangeAPI(ccxt.bitstamp(), self.config_manager)
        }
        self.arbitrage_analyzer = ArbitrageAnalyzer(self.config_manager)
        self.transaction_manager = {name: TransactionManager(exchange, self.config_manager) for name, exchange in self.exchanges.items()}
        self.data_storage = DataStorage(self.config_manager)

    async def execute_arbitrage_trade(self, opp):
        """Виконує арбітражну угоду на основі виявленої можливості."""
        buy_exchange = self.transaction_manager[opp['buy_exchange']]
        sell_exchange = self.transaction_manager[opp['sell_exchange']]
        
        # Перевірка ліквідності перед виконанням угоди
        if not buy_exchange.check_liquidity(opp['symbol'], opp['volume']) or \
           not sell_exchange.check_liquidity(opp['symbol'], opp['volume']):
            print(f"Insufficient liquidity for {opp['symbol']}")
            return

        try:
            # Створення замовлення на купівлю
            buy_order = await buy_exchange.create_buy_order(opp['symbol'], opp['volume'], opp['buy_price'])
            
            # Перевірка статусу замовлення на купівлю
            while not buy_exchange.is_order_filled(buy_order['id']):
                await asyncio.sleep(5)  # Перевірка кожні 5 секунд

            # Створення замовлення на продаж
            sell_order = await sell_exchange.create_sell_order(opp['symbol'], opp['volume'], opp['sell_price'])
            
            # Перевірка статусу замовлення на продаж
            while not sell_exchange.is_order_filled(sell_order['id']):
                await asyncio.sleep(5)  # Перевірка кожні 5 секунд

        except Exception as e:
            print(f"Error executing arbitrage trade: {e}")
            # Тут можна додати додаткову логіку для обробки помилок, наприклад, відміну невиконаних замовлень

    async def run_arbitrage(self):
        while True:
            for symbol in self.config_manager.get_currency_pairs():
                exchange_data = {}
                for name, exchange in self.exchanges.items():
                    ticker = await exchange.fetch_ticker(symbol)
                    exchange_data[name] = {
                        'buy_price': ticker['bid'],
                        'sell_price': ticker['ask']
                    }

                opportunities = self.arbitrage_analyzer.find_arbitrage_opportunity(exchange_data)
                for opp in opportunities:
                    self.arbitrage_analyzer.log_arbitrage_opportunity(opp)
                    await self.execute_arbitrage_trade(opp)

            await asyncio.sleep(self.config_manager.get_polling_interval())

    def start(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.run_arbitrage())

if __name__ == "__main__":
    app = CryptoArbitrage("config.json")
    app.start()
