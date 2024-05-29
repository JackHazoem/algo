class ConsolidationTradingAlgorithm(QCAlgorithm):
    def Initialize(self):
        # Set the start and end dates for the backtest
        self.SetStartDate(2022, 1, 1)
        self.SetEndDate(2023, 1, 1)
        
        # Set the initial cash balance
        self.SetCash(100000)
        
        # Add the SPY equity with daily resolution
        self.symbol = self.AddEquity("SPY", Resolution.Daily).Symbol
        
        # Lookback period to determine consolidation (20 days)
        self.lookback = 20
        
        # Range threshold for identifying consolidation (2%)
        self.range_threshold = 0.02  # 2% range considered as consolidation
        
        # Stop loss percentage
        self.stop_loss_pct = 0.01
        
        # Take profit percentage
        self.take_profit_pct = 0.02
        
        # Variable to store the consolidation zone
        self.consolidation_zone = None
        
        # Schedule an event to exit positions 15 minutes before market close each day
        self.Schedule.On(self.DateRules.EveryDay(self.symbol), self.TimeRules.BeforeMarketClose(self.symbol, 15), self.ExitPositions)
    
    def OnData(self, data):
        # Check if the data contains our symbol
        if not data.ContainsKey(self.symbol):
            return
        
        # Get the current price
        price = data[self.symbol].Close
        
        # Get historical data for the lookback period
        history = self.History(self.symbol, self.lookback, Resolution.Daily)
        
        # Return if the historical data is empty
        if history.empty:
            return
        
        # Calculate the highest and lowest prices in the lookback period
        high = history['high'].max()
        low = history['low'].min()
        
        # Calculate the current range as a percentage
        current_range = (high - low) / low
        
        # Determine if the current range falls within the consolidation threshold
        if current_range <= self.range_threshold:
            # Set the consolidation zone if within threshold
            self.consolidation_zone = (low, high)
        else:
            # Clear the consolidation zone if not within threshold
            self.consolidation_zone = None
        
        # Check if there is a defined consolidation zone
        if self.consolidation_zone:
            # If the price is at the bottom of the zone, go long
            if price <= self.consolidation_zone[0]:
                self.SetHoldings(self.symbol, 1)
                
                # Set stop loss and take profit orders
                self.StopLoss(self.symbol, price * (1 - self.stop_loss_pct))
                self.LimitOrder(self.symbol, -self.Portfolio[self.symbol].Quantity, price * (1 + self.take_profit_pct))
            # If the price is at the top of the zone, go short
            elif price >= self.consolidation_zone[1]:
                self.SetHoldings(self.symbol, -1)
                
                # Set stop loss and take profit orders
                self.StopLoss(self.symbol, price * (1 + self.stop_loss_pct))
                self.LimitOrder(self.symbol, self.Portfolio[self.symbol].Quantity, price * (1 - self.take_profit_pct))
    
    def ExitPositions(self):
        # Liquidate all positions
        self.Liquidate(self.symbol)
