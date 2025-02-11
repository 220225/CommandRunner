from dataclasses import dataclass, field

import matplotlib.pyplot as plt
import yfinance as yf

import Core

logger = Core.get_logger()


from CommandBase import CommandBase


@dataclass
class Cmd_Stock(CommandBase):
    label = "Stock"
    tooltip = "Show stock information by using Yahoo Finance API"

    stock_id: str = field(default="AAPL", metadata={"help": "Stock ID"})
    period: str = field(
        default="1mo",
        metadata={"help": "Period (year=1y, month=1mo, week=1wk, day=1d)"},
    )

    interval: str = field(
        default="1d",
        metadata={"help": "Interval (year=1y, month=1mo, week=1wk, day=1d)"}
    )

    def run(self, data={}):
        stock_id = data["stock_id"]
        period = data["period"]
        interval = data["interval"]

        # Get the data for the specified ticker
        ticker_data = yf.Ticker(stock_id)

        # Get the historical prices for this ticker
        hist = ticker_data.history(period=period, interval=interval)

        # Plot the closing prices
        plt.figure(figsize=(10, 5))
        plt.plot(hist.index, hist["Close"], label="Close Price")
        plt.title(f"{stock_id} Closing Prices")
        plt.xlabel("Date")
        plt.ylabel("Price")
        plt.legend()
        plt.grid(True)
        plt.show()
