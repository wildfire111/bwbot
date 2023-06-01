import math
class Transaction:
    # Mapping from token contract addresses to their symbol names
    TOKEN_ADDRESSES = {
        '0x82af49447d8a07e3bd95bd0d56f35241523fbab1': 'WETH',
        '0xda10009cbd5d07dd0cecc66161fc93d7c9000da1': 'DAI',
        '0xff970a61a04b1ca14834a43f5de4533ebddb5cc8': 'USDC',
        '0xfd086bc7cd5c481dcc9c85ebe478a1c0b69fcbb9': 'USDT',
        '0x2f2a2543b76a4166549f7aab2e75bef0aefc5b0f': 'WBTC',
        '0xfa7f8980b0f1e64a2062791cc3b0871572f1f7f0': 'UNI',
        '0xf97f4df75117a78c1a5a0dbb814af92458539fb4': 'LINK',
        '0x9d2f299715d94d8a7e6f5eaa8e654e8c74a988a7': 'FXS',
        '0x17fc002b466eec40dae837fc4be5c67993ddbd6f': 'FRAX',
        '0xfea7a6a0b346362bf88a9e4a88416b77a57d6c2a': 'MIM',
        'weth': 'WETH',
        'dai': 'DAI',
        'usdc': 'USDC',
        'usdt': 'USDT',
        'wbtc': 'WBTC',
        'uni': 'UNI',
        'link': 'LINK',
        'fxs': 'FXS',
        'frax': 'FRAX',
        'mim': 'MIM',
    }

    def __init__(self, account_address, collateral_type_hex, underlying_token_hex, price, collateral_delta, size_delta, fee, is_long, block_number, tx_hash):
        
        # Convert collateral type and underlying token from hex to symbol
        collateral_type = Transaction.TOKEN_ADDRESSES.get(collateral_type_hex.lower(), None)
        if not collateral_type:
            raise ValueError("Invalid collateral type.")

        underlying_token = Transaction.TOKEN_ADDRESSES.get(underlying_token_hex.lower(), None)
        if not underlying_token:
            raise ValueError("Invalid underlying token.")

        self.account_address = account_address
        self.collateral_type = collateral_type
        self.underlying_token = underlying_token
        self.price = price
        self.collateral_delta = collateral_delta
        self.size_delta = size_delta
        self.fee = fee
        self.is_long = is_long
        self.block_number = block_number
        self.tx_hash = tx_hash
        
    def get_sql_query(self):
        # Define the SQL statement for inserting a new transaction
        add_transaction = ("INSERT INTO transactions "
                            "(account_address, collateral_type, underlying_token, price, collateral_delta, size_delta, fee, is_long, block_number, tx_hash) "
                            "VALUES (\"%s\", \"%s\", \"%s\", %s, %s, %s, %s, %s, %s, \"%s\")")

        # Generate the SQL query with the transaction data
        transaction_data = (self.account_address, self.collateral_type, self.underlying_token, self.price, self.collateral_delta,
                            self.size_delta, self.fee, self.is_long, self.block_number, self.tx_hash)
        sql_query = add_transaction % transaction_data
        return sql_query

    def __str__(self):
        return (
            f"Transaction(account_address={self.account_address}, "
            f"collateral_type={self.collateral_type}, "
            f"underlying_token={self.underlying_token}, "
            f"price={self.price}, "
            f"collateral_delta={self.collateral_delta}, "
            f"size_delta={self.size_delta}, "
            f"fee={self.fee}, "
            f"is_long={self.is_long}, "
            f"block_number={self.block_number}, "
            f"tx_hash={self.tx_hash})"
        )

    def __repr__(self):
        return self.__str__()

class Trade:
    def __init__(self, finalized_block, start_price, end_price, size_in_dollars, collateral):
        self.finalized_block = finalized_block
        self.start_price = start_price
        self.end_price = end_price
        self.size_in_dollars = size_in_dollars
        self.collateral = collateral
    
    def get_profit(self):
        return (self.end_price - self.start_price) * self.size_in_units()
    
    def size_in_units(self):
        return self.size_in_dollars / self.start_price
    
    def get_profit_percentage(self):
        return (self.get_profit() / self.collateral) * 100
    
    def __str__(self):
        return f"Trade: Profit = {self.get_profit_percentage():.2f}%, Start Price = {self.start_price:.2f}, End Price = {self.end_price:.2f}, Size = {self.size_in_dollars:.2f}, Collateral = {self.collateral:.2f}, Finalized_block={self.finalized_block}"



class Trader:
    def __init__(self, account_address, trades):
        self.account_address = account_address
        self.trades = trades
    
    def get_total_profit(self):
        total_profit = 0
        for trade in self.trades:
            total_profit += trade.get_profit()
        return total_profit
    
    def get_average_profit_percentage(self):
        total_profit_percentage = 0
        for trade in self.trades:
            total_profit_percentage += trade.get_profit_percentage()
        return total_profit_percentage / len(self.trades)
    
    def get_profitable_trades_percentage(self):
        profitable_trades = [trade for trade in self.trades if trade.get_profit() > 0]
        return (len(profitable_trades) / len(self.trades)) * 100
    
    
    def get_sharpe_ratio(self, risk_free_rate):
        total_profit = self.get_total_profit()
        total_return = total_profit / sum(trade.collateral for trade in self.trades)
        std_dev = math.sqrt(sum(math.pow(trade.get_profit_percentage() / 100 - total_return, 2) for trade in self.trades) / len(self.trades))
        sharpe_ratio = (total_return - risk_free_rate) / std_dev
        return sharpe_ratio
    
    def get_sortino_ratio(self, threshold):
        total_profit = self.get_total_profit()
        total_return = total_profit / sum(trade.collateral for trade in self.trades)
        downside_returns = [(trade.get_profit_percentage() / 100 - total_return) for trade in self.trades if trade.get_profit_percentage() / 100 < threshold]
        downside_deviation = math.sqrt(sum([x ** 2 for x in downside_returns]) / len(downside_returns))
        sortino_ratio = (total_return - threshold) / downside_deviation
        return sortino_ratio
    
    def get_treynor_ratio(self, market_return):
        total_profit = self.get_total_profit()
        total_return = total_profit / sum(trade.collateral for trade in self.trades)
        beta = sum([(trade.get_profit_percentage() / 100 - total_return) * (market_return - total_profit / sum(trade.collateral for trade in self.trades)) for trade in self.trades]) / sum([(market_return - total_profit / sum(trade.collateral for trade in self.trades)) ** 2 for trade in self.trades])
        treynor_ratio = (total_return - market_return) / beta
        return treynor_ratio
    
    def get_information_ratio(self, benchmark_returns):
        total_profit = self.get_total_profit()
        total_return = total_profit / sum(trade.collateral for trade in self.trades)
        active_returns = [trade.get_profit_percentage() / 100 - benchmark_returns[i] for i, trade in enumerate(self.trades)]
        tracking_error = math.sqrt(sum([x ** 2 for x in active_returns]) / len(active_returns))
        information_ratio = sum(active_returns) / tracking_error
        return information_ratio
    
    def get_win_loss_ratio(self):
        winning_trades = [trade for trade in self.trades if trade.get_profit() > 0]
        losing_trades = [trade for trade in self.trades if trade.get_profit() < 0]
        win_loss_ratio = len(winning_trades) / len(losing_trades) if len(losing_trades) > 0 else float('inf')
        return win_loss_ratio
    
    def get_omega_ratio(self):
        positive_returns = [trade for trade in self.trades if trade.get_profit() > 0]
        negative_returns = [trade for trade in self.trades if trade.get_profit() < 0]
        p_plus = len(positive_returns) / len(self.trades)
        p_minus = len(negative_returns) / len(self.trades)
        omega_ratio = p_plus / (1 - p_minus) if p_minus < 1 else float('inf')
        return omega_ratio


