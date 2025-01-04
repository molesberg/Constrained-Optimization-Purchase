import numpy as np
import random
import time

# Define the data
buy_dict = {
    "a.com": {},
    "b.com": {},
    "c.com": {},
    "d.com": {},
    "e.com": {}
}
websites = buy_dict.keys()
#randomized data
np.random.seed(42)
random.seed(42)
prices = np.random.uniform(0.35, 40, size=(100, 5))
prices = np.ceil(prices * 100) / 100  # round prices to 2 decimal places
quantities = np.random.randint(1, 6, size=100)
budgets = np.random.rand(5)*500

# Initialize variables to keep track of the supplies bought and the remaining budget
supplies_bought = np.zeros((len(prices), len(websites)), dtype=int)
remaining_budget = budgets.copy()

# Calculate the marginal cost of each supply
marginal_costs = np.zeros((len(prices), len(websites)))
for i in range(len(prices)):
    for j in range(len(websites)):
        min_price_idx = np.nanargmin(prices[i])
        if j == min_price_idx:
            marginal_costs[i, j] = 0
        else:
            marginal_costs[i, j] = prices[i, j] - prices[i, min_price_idx]

while sum(remaining_budget) > 5 and sum(quantities) > 0: #general case
#while remaining_budget[3] > 0 and sum(quantities) > 0: #Use this specific case if you know one website has a lot more resources avaliable and usually doesn't use all the money
    #Mask by websites which have money remaining
    lowest_price = np.nanmin(prices, axis = 0)
    mask_column = remaining_budget - lowest_price <= 0
    mask_row = quantities > 0
    masked_marginal_costs = marginal_costs[:, ~mask_column]
    masked_marginal_costs = masked_marginal_costs[mask_row, :]
    masked_prices = prices[:, ~mask_column]
    masked_prices = masked_prices[mask_row, :]
    masked_remaining_budget = remaining_budget[~mask_column]
    masked_cols = np.where(~mask_column)[0]
    masked_rows = np.where(mask_row)[0]

    if np.all(np.isnan(masked_prices)): #The websites with remaining value have no valid purchases
        break
    #Generate a vector of the price saved buying the cheapest version avaliable compared to the second cheapest
    if len(masked_remaining_budget) > 2:
        # savings_to_next_lowest_values = np.partition(masked_marginal_costs, 2, axis=1)[:, 1] - np.nanmin(masked_marginal_costs, axis=1) #straight difference
        savings_to_next_lowest_values = (np.partition(masked_marginal_costs, 2, axis=1)[:, 1] - np.nanmin(masked_marginal_costs, axis=1))/np.nanmin(masked_prices, axis=1) #difference normalized by cost
        #The logic of normalizing the savings is that buying an item with quantity 2 which costs $4 and the next cheapest version is $5
        #Saves $2 when buying an item with quantity 1 which costs $8.50 and the next cheapest is $10 saves more per unit ($1) but less for how much money we spent ($1.50)
    
    else: #when there are only two websites left
        # savings_to_next_lowest_values = np.nanmax(masked_marginal_costs, axis=1) - np.nanmin(masked_marginal_costs, axis=1)
        savings_to_next_lowest_values = (np.nanmax(masked_marginal_costs, axis=1) - np.nanmin(masked_marginal_costs, axis=1))/np.nanmin(masked_marginal_costs, axis=1) #normalized
    #Identify the row with the greatest marginal savings and the website it comes from
    #Need an except for all nan slice when no one can afford to buy an item
    if np.size(masked_remaining_budget) == 1:
        best_buy_idx = np.nanargmax(masked_prices)
        best_buy_source = 0
    else:
        best_buy_idx = np.nanargmax(savings_to_next_lowest_values) #acts as our row
        best_buy_source = np.nanargmin(masked_marginal_costs[best_buy_idx, :]) #acts as our column

    ##If the savings are 0 or nan, apply it to the website with the most credit left 
    if np.nanmax(savings_to_next_lowest_values) == 0:
        temp_mask = masked_marginal_costs[best_buy_idx, :] == 0
        filtered_sites = masked_remaining_budget[temp_mask]
        if len(filtered_sites) == 0: #when there are only marginal costs > 0 and nan
            best_buy_source = np.nanargmin(masked_marginal_costs[best_buy_idx, :])
        else: #normal case
            max_index = np.argmax(filtered_sites)
            original_index = np.where(temp_mask)[0][max_index]
            best_buy_source = original_index

    #Calculate how many we can buy, assuming we can go up to $10 over 
    max_quantity = int((masked_remaining_budget[best_buy_source] + 10 )/ masked_prices[best_buy_idx, best_buy_source])
    # Buy the minimum of the maximum quantity and the required quantity
    masked_quantities = quantities[mask_row]
    quantity_to_buy = min(max_quantity, masked_quantities[best_buy_idx]) #This should return 0 if we cannot buy one fully
    quantity_to_buy - max(quantity_to_buy, 0) #To avoid a negative quantity to buy

    #For cases were the best value is to buy from a site which doesn't have money left
    if quantity_to_buy == 0:
        prices[masked_rows[best_buy_idx], masked_cols[best_buy_source]] = np.nan
        #Reset marginal values
        for j in range(len(websites)):
            min_price_idx = np.nanargmin(prices[masked_rows[best_buy_idx]])
            if j == min_price_idx:
                marginal_costs[masked_rows[best_buy_idx], j] = 0
            else:
                marginal_costs[masked_rows[best_buy_idx], j] = prices[masked_rows[best_buy_idx], j] - prices[masked_rows[best_buy_idx], min_price_idx]
    else: #Normal purchase case
        supplies_bought[masked_rows[best_buy_idx], masked_cols[best_buy_source]] = quantity_to_buy
        remaining_budget[masked_cols[best_buy_source]] -= quantity_to_buy * masked_prices[best_buy_idx, best_buy_source]
        quantities[masked_rows[best_buy_idx]] -= quantity_to_buy


print(remaining_budget)
print(supplies_bought) #Columns are each website , rows are how many of each supply they bought
print("Finished at " + time.ctime())