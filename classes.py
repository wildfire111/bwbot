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
    }

    def __init__(
        self,
        account_address: str,
        collateral_type_hex: str,
        underlying_token_hex: str,
        price: float,
        collateral_delta: float,
        size_delta: float,
        fee: float,
        direction: str,
        block_number: int,
        tx_hash: str,
    ):
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
        self.direction = direction
        self.block_number = block_number
        self.tx_hash = tx_hash

    def __str__(self):
        return (
            f"Trade(account_address={self.account_address}, "
            f"collateral_type={self.collateral_type}, "
            f"underlying_token={self.underlying_token}, "
            f"price={self.price}, "
            f"collateral_delta={self.collateral_delta}, "
            f"size_delta={self.size_delta}, "
            f"fee={self.fee}, "
            f"direction={self.direction}, "
            f"block_number={self.block_number}, "
            f"tx_hash={self.tx_hash})"
        )

    def __repr__(self):
        return self.__str__()
