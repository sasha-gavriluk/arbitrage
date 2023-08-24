import os
import time

start_time = time.time()

# Ваші класи
from utility.arbitrage_file import ExchangeAPI, ArbitrageAnalyzer, ConfigManager, TransactionManager, NotificationManager, SimulationTrading

path_file = os.path.abspath(os.path.dirname(__file__))
path_congfig = os.path.join(path_file, "config/config.json")
config = ConfigManager(path_congfig)

exchange_api = ExchangeAPI(config)
transaction = TransactionManager(exchange_api)
arbitrage_analyzer = ArbitrageAnalyzer(exchange_api, config)

opportunities = arbitrage_analyzer.find_opportunities(['bybit', 'bitstamp'])

# 2. Створення екземпляра SimulationTrading
initial_balance = 6000  # Початковий баланс для імітаційної торгівлі
simulation_trading = SimulationTrading(exchange_api, arbitrage_analyzer, transaction, initial_balance)

simulation_trading.run_simulation(['bybit', 'bitstamp'])

elapsed_time = time.time() - start_time
mins, secs = divmod(elapsed_time, 60)
time_format = "{:0>2}:{:0>5.2f}".format(int(mins), secs)
print(time_format, end='\r')

"""

# Пошук можливостей для арбітражу між біржами 'binance' та 'coinbase'
opportunities = arbitrage_analyzer.find_opportunities(['bybit', 'bitstamp'])
#transaction.execute_best_trade(opportunities)

filtered_opportunities = arbitrage_analyzer.filter_liquid_markets(opportunities)
print(filtered_opportunities)

print('\n')


send_message = NotificationManager()

# Ініціалізація ArbitrageAnalyzer

# Фільтрація можливостей на основі ліквідності (зараз просто повертає всі можливості)
filtered_opportunities = analyzer.filter_liquid_markets(opportunities)
print(filtered_opportunities)
print('\n')


# Розрахунок прибутку для першої можливості
if filtered_opportunities:
    profit = analyzer.calculate_profit(filtered_opportunities[0])
    print(f"Potential profit: {profit}")

    # Розрахунок комісій для першої можливості
    fees = analyzer.estimate_transaction_fees(filtered_opportunities[0])
    print(f"Estimated fees: {fees}")
print('\n')

exchange_name = ["bybit","bitstamp"]
for name in exchange_name:
    print(exchange_api.get_balance(name))

print('\n')

send_message.send_alert("Угода виконна! Удачно.")
"""