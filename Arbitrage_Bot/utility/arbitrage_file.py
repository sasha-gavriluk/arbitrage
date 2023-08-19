import json
import random
import shutil
import os
import datetime
import logging
import ccxt

from collections import defaultdict


def setup_class_logger(class_name):
    path_py_file = os.path.abspath(os.path.dirname(os.path.dirname(__name__)))
    path_file_log = os.path.join(path_py_file, f'logs/{class_name}.log')

    logger = logging.getLogger(class_name)
    handler = logging.FileHandler(path_file_log)
    formatter = logging.Formatter('[%(asctime)s][%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger


class ExchangeAPI:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.exchanges_config = self.config_manager.get("exchanges", {})
        self.logger = setup_class_logger(self.__class__.__name__)
        self.exchanges = self._initialize_exchanges()
        self.cache = {}

    def _initialize_exchanges(self):
        initialized_exchanges = {}
        for exchange_name, config in self.exchanges_config.items():
            try:
                exchange_class = getattr(ccxt, exchange_name)
                initialized_exchanges[exchange_name] = exchange_class({
                    'apiKey': config['api_key'],
                    'secret': config['api_secret']
                })
                self.logger.info(f"Initialized {exchange_name} successfully.")
            except Exception as e:
                self.logger.error(f"Error initializing {exchange_name}: {str(e)}")
        return initialized_exchanges

    def get_price(self, coin, exchange_name):
        cache_key = f'{coin}_{exchange_name}_price'
        if cache_key in self.cache:
            return self.cache[cache_key]
        exchange = self.exchanges.get(exchange_name)
        if not exchange:
            raise ValueError(f"Exchange {exchange_name} not found.")
        ticker = exchange.fetch_ticker(coin)
        self.cache[cache_key] = ticker['last']
        self.logger.info(f"Fetched price for {coin} from {exchange_name}: {ticker['last']}")
        return ticker['last']

    def buy(self, coin, amount, exchange_name, order_type='market'):
        exchange = self.exchanges.get(exchange_name)
        if not exchange:
            raise ValueError(f"Exchange {exchange_name} not found.")
        if order_type == 'market':
            order = exchange.create_market_buy_order(coin, amount)
        elif order_type == 'limit':
            # For simplicity, assuming a fixed price for limit orders
            price = self.get_price(coin, exchange_name) * 1.01  # 1% above the current price
            order = exchange.create_limit_buy_order(coin, price, amount)
        else:
            raise ValueError(f'Unsupported order type: {order_type}')
        self.logger.info(f"Bought {amount} of {coin} on {exchange_name} using {order_type} order.")
        return order

    def sell(self, coin, amount, exchange_name, order_type='market'):
        exchange = self.exchanges.get(exchange_name)
        if not exchange:
            raise ValueError(f"Exchange {exchange_name} not found.")
        if order_type == 'market':
            order = exchange.create_market_sell_order(coin, amount)
        elif order_type == 'limit':
            # For simplicity, assuming a fixed price for limit orders
            price = self.get_price(coin, exchange_name) * 0.99  # 1% below the current price
            order = exchange.create_limit_sell_order(coin, price, amount)
        else:
            raise ValueError(f'Unsupported order type: {order_type}')
        self.logger.info(f"Sold {amount} of {coin} on {exchange_name} using {order_type} order.")
        return order

    def get_order_book(self, coin, exchange_name):
        exchange = self.exchanges.get(exchange_name)
        if not exchange:
            raise ValueError(f"Exchange {exchange_name} not found.")
        order_book = exchange.fetch_order_book(coin)
        return order_book

    def get_balance(self, exchange_name):
        exchange = self.exchanges.get(exchange_name)
        if not exchange:
            raise ValueError(f"Exchange {exchange_name} not found.")
        balance = exchange.fetch_balance()
        return balance

    def get_all_prices(self, coin):
        prices = {}
        for exchange_name, exchange in self.exchanges.items():
            price = self.get_price(coin, exchange_name)
            prices[exchange_name] = price
        return prices

    def compare_prices(self, coin):
        prices = self.get_all_prices(coin)
        best_buy = min(prices, key=prices.get)
        best_sell = max(prices, key=prices.get)
        return {'best_buy': best_buy, 'best_sell': best_sell}

    def get_best_exchange_for_buy(self, coin):
        prices = self.get_all_prices(coin)
        return min(prices, key=prices.get)

    def get_best_exchange_for_sell(self, coin):
        prices = self.get_all_prices(coin)
        return max(prices, key=prices.get)
    
    def get_common_currency_pairs(self, exchange_list):
        # 1. Отримання параметрів з config
        selected_assets = self.config_manager.get('currency_pairs', {}).get('selected_assets', [])
        top_n = self.config_manager.get('currency_pairs', {}).get('top_n', 10)

        common_pairs = {}
        
        # 2. Провірка на список
        if selected_assets:
            # Якщо список не пустий, повертаємо його
            for i in range(len(exchange_list)):
                for j in range(i+1, len(exchange_list)):
                    pair_name = f'{exchange_list[i]}_{exchange_list[j]}'
                    common_pairs[pair_name] = [pair for pair in selected_assets if pair in self.exchanges.get(exchange_list[i]).load_markets().keys() and pair in self.exchanges.get(exchange_list[j]).load_markets().keys()]
        else:
            # Якщо список пустий, заповнюємо його автоматично
            for i in range(len(exchange_list)):
                for j in range(i+1, len(exchange_list)):
                    exchange_1 = self.exchanges.get(exchange_list[i])
                    exchange_2 = self.exchanges.get(exchange_list[j])
                    if not exchange_1 or not exchange_2:
                        continue
                    pairs_1 = set(exchange_1.load_markets().keys())
                    pairs_2 = set(exchange_2.load_markets().keys())
                    common = list(pairs_1.intersection(pairs_2))[:top_n]
                    pair_name = f'{exchange_list[i]}_{exchange_list[j]}'
                    common_pairs[pair_name] = common

        return common_pairs
    
    def close_logger(self):
        for handler in self.logger.handlers:
            handler.close()
            self.logger.removeHandler(handler)
    
class ArbitrageAnalyzer:
    def __init__(self, exchange_api, config_manager):
        self.logger = setup_class_logger(self.__class__.__name__)
        self.exchange_api = exchange_api
        self.config_manager = config_manager
        self.arbitrage_config = config_manager.get_arbitrage_config()

    def find_opportunities(self, exchanges):
        opportunities = []
        common_pairs = self.exchange_api.get_common_currency_pairs(exchanges)
        min_price_difference = self.arbitrage_config.get("min_price_difference", 0.01)
        
        for pair, currencies in common_pairs.items():
            for currency in currencies:
                exchange_1, exchange_2 = pair.split('_')
                price_1 = self.exchange_api.get_price(currency, exchange_1)
                price_2 = self.exchange_api.get_price(currency, exchange_2)
                if abs(price_1 - price_2) >= min_price_difference:
                    if price_1 < price_2:
                        opportunities.append({
                            'buy_exchange': exchange_1,
                            'sell_exchange': exchange_2,
                            'currency': currency,
                            'buy_price': price_1,
                            'sell_price': price_2
                        })
                    else:
                        opportunities.append({
                            'buy_exchange': exchange_2,
                            'sell_exchange': exchange_1,
                            'currency': currency,
                            'buy_price': price_2,
                            'sell_price': price_1
                        })

        self.logger.info(f"Found {len(opportunities)} arbitrage opportunities.")
        return opportunities

    def estimate_transaction_fees(self, opportunity):
        transaction_fee = self.config_manager.get_transaction_fee()
        return transaction_fee * opportunity['buy_price']

    def filter_liquid_markets(self, opportunities):
        # Placeholder for filtering based on market liquidity
        # For now, returning all opportunities
        return opportunities

    def calculate_profit(self, opportunity):
        buy_price = opportunity['buy_price']
        sell_price = opportunity['sell_price']
        return sell_price - buy_price
    
    def close_logger(self):
        for handler in self.logger.handlers:
            handler.close()
            self.logger.removeHandler(handler)

class TransactionManager:
    def __init__(self, exchange_api):
        self.exchange_api = exchange_api
        self.logger = setup_class_logger(self.__class__.__name__)

    def execute_trade(self, opportunity):
        # Виконуємо купівлю на біржі з найнижчою ціною
        buy_order = self.exchange_api.buy(
            opportunity['currency'], 
            opportunity['amount'], 
            opportunity['buy_exchange']
        )

        # Виконуємо продаж на біржі з найвищою ціною
        sell_order = self.exchange_api.sell(
            opportunity['currency'], 
            opportunity['amount'], 
            opportunity['sell_exchange']
        )

        # Повертаємо інформацію про обидві транзакції
        self.logger.info(f"Executed trade: Buy {opportunity['currency']} on {opportunity['buy_exchange']} and sell on {opportunity['sell_exchange']}.")
        return {
            'buy_order': buy_order,
            'sell_order': sell_order
        }

    def log_transaction(self, transaction):
        self.logger.info(f"Executed BUY order: {transaction['buy_order']}")
        self.logger.info(f"Executed SELL order: {transaction['sell_order']}")

    def get_best_opportunity(self, opportunities):
        # Вибираємо найкращу можливість на основі різниці в цінах
        best_opportunity = max(opportunities, key=lambda x: x['sell_price'] - x['buy_price'])
        return best_opportunity

    def execute_best_trade(self, opportunities):
        # Перевірка, чи є можливості для арбітражу
        if not opportunities:
            print("No arbitrage opportunities found.")
            return None

        best_opportunity = self.get_best_opportunity(opportunities)
        
        # Перевірка, чи є різниця в цінах позитивною (арбітраж можливий)
        if best_opportunity['sell_price'] <= best_opportunity['buy_price']:
            print("No profitable arbitrage opportunity found.")
            return None

        transaction = self.execute_trade(best_opportunity)
        self.log_transaction(transaction)
        return transaction
    
    def close_logger(self):
        for handler in self.logger.handlers:
            handler.close()
            self.logger.removeHandler(handler)

class DataManager:
    def __init__(self, data_file="price_data.json"):
        self.logger = setup_class_logger(self.__class__.__name__)
        self.data_file = data_file
        if not os.path.exists(self.data_file):
            with open(self.data_file, 'w') as file:
                json.dump({}, file)

    def store_price_data(self, data):
        """Зберігає історію цін."""
        with open(self.data_file, 'r') as file:
            existing_data = json.load(file)
        self.logger.info(f"Stored price data for {len(data)} coins.")
        
        # Оновлюємо існуючі дані новими
        existing_data.update(data)
        
        with open(self.data_file, 'w') as file:
            json.dump(existing_data, file)

    def get_price_history(self, coin):
        """Отримує історію цін валюти."""
        with open(self.data_file, 'r') as file:
            data = json.load(file)
        self.logger.info(f"Fetched price history for {coin}.")
        return data.get(coin, [])
    
    def close_logger(self):
        for handler in self.logger.handlers:
            handler.close()
            self.logger.removeHandler(handler)

class SecurityManager:
    def encrypt_data(self, data):
        pass

    def detect_suspicious_activity(self):
        pass

class NotificationManager:
    def __init__(self, logger):
        self.logger = setup_class_logger(self.__class__.__name__)

    def send_alert(self, message):
        # Тут можна додати код для відправлення сповіщення користувачеві.
        # Наприклад, відправлення електронного листа, SMS або іншого типу сповіщення.
        # Для прикладу, просто виведемо повідомлення на екран:
        self.logger.info(f"Sent alert: {message}")
        print(f"ALERT: {message}")

    def log_event(self, event):
        # Логуємо подію за допомогою переданого логера
        self.logger.info(event)

    def close_logger(self):
        for handler in self.logger.handlers:
            handler.close()
            self.logger.removeHandler(handler)


class ConfigManager:

    def __init__(self, config_file):
        self.config_file = config_file
        self.config_data = self.load_config()
        self.logger = setup_class_logger(self.__class__.__name__)

    def load_config(self):
        with open(self.config_file, 'r') as file:
            return json.load(file)

    def update_config(self, new_config):
        with open(self.config_file, 'w') as file:
            json.dump(new_config, file, indent=4)
        self.config_data = new_config

    def get(self, key, default=None):
        return self.config_data.get(key, default)

    def create_backup(self):
        backup_location = self.get("backup.backup_location")
        if not backup_location:
            self.logger.warning("Backup location is not specified in the config.")
            return

        if not os.path.exists(backup_location):
            os.makedirs(backup_location)

        backup_file = os.path.join(backup_location, f"config_backup_{os.path.basename(self.config_file)}")
        shutil.copy(self.config_file, backup_file)
        self.logger.info(f"Backup created at {backup_file}")

    def restore_backup(self, backup_path):
        if not os.path.exists(backup_path):
            self.logger.info("Backup file does not exist.")
            return

        shutil.copy(backup_path, self.config_file)
        self.config_data = self.load_config()
        self.logger.info("Config restored from backup.")

    def get_logging_config(self):
        return self.get("logging", {})

    def get_transaction_fee(self):
        return self.get("transaction.fee", 0.001)

    def get_arbitrage_config(self):
        return self.get("arbitrage", {})

    def get_currency_pairs_config(self):
        return self.get("currency_pairs", {})

    def close_logger(self):
        for handler in self.logger.handlers:
            handler.close()
            self.logger.removeHandler(handler)

class SimulationTrading:

    def __init__(self, exchange_api, arbitrage_analyzer, initial_balance):
        self.exchange_api = exchange_api
        self.logger = setup_class_logger(self.__class__.__name__)
        self.arbitrage_analyzer = arbitrage_analyzer
        self.conversion_prices = {}
        self.exchanges = self.convert_balance(initial_balance)
        self.total_balance = initial_balance * len(self.exchanges)

    def convert_balance(self, initial_balance):
        exchange_balances = {}
        exchange_list = list(self.exchange_api.exchanges.keys())

        common_pairs_dict = self.exchange_api.get_common_currency_pairs(exchange_list)
        currency_pairs = []

        for pairs in common_pairs_dict.values():
            currency_pairs.extend(pairs)

        for exchange in exchange_list:
            balances = {}
            balance = initial_balance  # Початковий баланс для кожної біржі
            portion_balance = initial_balance / len(currency_pairs)
            
            for pair in currency_pairs:
                base_currency, quote_currency = pair.split('/')

                # Визначаємо, яка валюта є "основною"
                if quote_currency in ["USDT", "USD"]:
                    main_currency = base_currency
                elif base_currency in ["USDT", "USD"]:
                    main_currency = quote_currency
                else:
                    main_currency = base_currency  # або quote_currency, залежно від вашої логіки

                # Тепер отримуємо ціну для "основної" валюти відносно USD
                if main_currency != "USDT":
                    main_price = self.exchange_api.get_price(main_currency + "/USDT", exchange)
                    # Зберігаємо ціну конвертації для подальшого використання
                    if exchange not in self.conversion_prices:
                        self.conversion_prices[exchange] = {}
                    self.conversion_prices[exchange][main_currency] = main_price
                    main_amount = portion_balance / main_price
                    balances[main_currency] = balances.get(main_currency, 0) + main_amount
                    balance -= portion_balance  # Віднімаємо суму, яку ми конвертували

                    
            final_balances = {"balance": balance}
            final_balances.update(balances)
            exchange_balances[exchange] = final_balances

        return exchange_balances


    def revert_to_dollars(self):
        for exchange, balances in self.exchanges.items():
            initial_balance = balances["balance"]  # Зберігаємо початковий баланс
            total_converted = 0  # Сума, яку ми конвертуємо в інші валюти

            for currency, amount in balances.items():
                if currency != "balance":
                    conversion_price = self.conversion_prices[exchange].get(currency, 1)  # 1 як default для USDT/USD
                    total_converted += amount * conversion_price  # Додаємо до загальної суми

            # Відновлюємо баланс
            balances["balance"] = initial_balance + total_converted
            for currency in balances:
                if currency != "balance":
                    balances[currency] = 0  # Зануляємо баланс валюти після конвертації
                    
        return self.exchanges
    
    def run_simulation(self):
        logging.info("Starting the simulation...")

        # Крок 1: Виконання торгових операцій
        logging.info("Step 1: Executing trading operations...")
        opportunities = self.arbitrage_analyzer.find_opportunities()
        if not opportunities:
            logging.warning("No arbitrage opportunities found.")
        for op in opportunities:
            # Симулюємо покупку
            logging.info(f"Simulating buying {op['buy_amount']} {op['buy_currency']} on {op['buy_exchange']} at price {op['buy_price']} USDT.")
            self.simulate_buy(op['buy_currency'], op['buy_amount'], opportunities)
            
            # Симулюємо продаж
            logging.info(f"Simulating selling {op['sell_amount']} {op['sell_currency']} on {op['sell_exchange']} at price {op['sell_price']} USDT.")
            self.simulate_sell(op['sell_currency'], op['sell_amount'], opportunities)

        # Крок 2: Відновлення балансу до доларів
        logging.info("Step 2: Reverting all currencies back to USDT...")
        for exchange in self.exchanges:
            for currency, amount in self.exchanges[exchange].items():
                if currency != "balance" and amount > 0:
                    logging.info(f"Converting {amount} {currency} back to USDT on {exchange}.")
                    self.simulate_sell(currency, amount, opportunities)

        # Крок 3: Виведення результатів симуляції
        total_balance = sum([self.exchanges[exchange]["balance"] for exchange in self.exchanges])
        logging.info(f"Step 3: Simulation completed. Total balance after simulation: {total_balance} USDT.")


    def simulate_trade(self, opportunity, commission_rate=0.0025):
        buy_exchange, sell_exchange, buy_price, sell_price, amount = opportunity

        # Врахування комісії
        buy_amount_after_commission = amount * (1 - commission_rate)
        sell_amount_after_commission = amount * (1 - commission_rate)

        # Врахування цінових розбіжностей (наприклад, 0.5% випадковості)
        buy_price_variation = buy_price * (1 + random.uniform(-0.005, 0.005))
        sell_price_variation = sell_price * (1 + random.uniform(-0.005, 0.005))

        # Імітація купівлі
        self.simulation_balances[buy_exchange]['USDT'] -= buy_price_variation * buy_amount_after_commission
        self.simulation_balances[buy_exchange]['BTC'] += buy_amount_after_commission

        # Імітація продажу
        self.simulation_balances[sell_exchange]['BTC'] -= sell_amount_after_commission
        self.simulation_balances[sell_exchange]['USDT'] += sell_price_variation * sell_amount_after_commission

        return True

    def simulate_sell(self, currency, amount, opportunities):
        # Знаходимо можливість для продажу валюти
        sell_opportunity = next((op for op in opportunities if op['sell_currency'] == currency), None)
        
        if not sell_opportunity:
            logging.warning(f"No sell opportunity found for {currency}")
            return

        sell_price = sell_opportunity['sell_price']
        usdt_amount = amount * sell_price
        self.exchanges[sell_opportunity['sell_exchange']]["balance"] += usdt_amount
        self.exchanges[sell_opportunity['sell_exchange']][currency] -= amount

    def simulate_buy(self, currency, amount, opportunities):
        # Знаходимо можливість для покупки валюти
        buy_opportunity = next((op for op in opportunities if op['buy_currency'] == currency), None)
        
        if not buy_opportunity:
            logging.warning(f"No buy opportunity found for {currency}")
            return

        buy_price = buy_opportunity['buy_price']
        usdt_amount = amount * buy_price
        if self.exchanges[buy_opportunity['buy_exchange']]["balance"] >= usdt_amount:
            self.exchanges[buy_opportunity['buy_exchange']]["balance"] -= usdt_amount
            self.exchanges[buy_opportunity['buy_exchange']][currency] += amount