import requests
import random
import heapq

def get_exchange_rates(api_key):
    url = f'https://v6.exchangerate-api.com/v6/{api_key}/latest/USD'  # Replace 'USD' with the base currency of your choice
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")
        return None

def generate_random_tax():
    return random.uniform(0.01, 0.05)  # Generate a random tax between 1% and 5%

def generate_price_volatility():
    # Generates a volatility factor that can decrease or increase the base rate by up to 5%
    return 1 + random.uniform(-0.05, 0.05)

def create_graph(exchange_rates, available_pairs):
    graph = {}
    conversion_rates = {}
    for currency, rate in exchange_rates['conversion_rates'].items():
        graph[currency] = {}
        conversion_rates[currency] = {}
        for target_currency in available_pairs.get(currency, []):
            if target_currency in exchange_rates['conversion_rates']:
                base_target_rate = exchange_rates['conversion_rates'][target_currency]
                conversion_rate = base_target_rate / rate

                volatile_rate = conversion_rate * (generate_price_volatility())

                # Calculate tax
                tax = generate_random_tax()
                effective_rate = volatile_rate * (1 - tax)  # Reduce rate by tax

                # Store the effective rate that maximizes the conversion value
                graph[currency][target_currency] = effective_rate
                conversion_rates[currency][target_currency] = (volatile_rate, tax, effective_rate)
    return graph, conversion_rates

def heuristic(current, goal, exchange_rates):
    if current == goal:
        return 0
    
    current_to_usd = 1 / exchange_rates['conversion_rates'][current]
    goal_to_usd = 1 / exchange_rates['conversion_rates'][goal]
    estimated_cost = abs(current_to_usd - goal_to_usd)

    return estimated_cost

def a_star_search(graph, start, goal, exchange_rates):
    open_list = []
    heapq.heappush(open_list, (1, start))  # Start with an inverted rate of 1 (which represents no change)
    came_from = {}
    cost_so_far = {start: 1}  # Initialize with 1, meaning no conversion has taken place

    while open_list:
        current_inv_rate, current = heapq.heappop(open_list)

        if current == goal:
            break

        for neighbor, rate in graph[current].items():
            new_inv_rate = current_inv_rate * (1 / rate)  # Invert and multiply rates
            if neighbor not in cost_so_far or new_inv_rate < cost_so_far[neighbor]:  # Minimize the inverted rates
                cost_so_far[neighbor] = new_inv_rate
                priority = new_inv_rate * heuristic(neighbor, goal, exchange_rates)  # Adjust priority accordingly
                heapq.heappush(open_list, (priority, neighbor))
                came_from[neighbor] = current

    return came_from, cost_so_far

def reconstruct_path(came_from, start, goal):
    current = goal
    path = []
    while current != start:
        path.append(current)
        current = came_from[current]
    path.append(start)
    path.reverse()
    return path

def find_all_paths(graph, start, goal, path=[]):
    path = path + [start]
    if start == goal:
        return [path]
    if start not in graph:
        return []
    paths = []
    for neighbor in graph[start]:
        if neighbor not in path:  # Avoid cycles
            newpaths = find_all_paths(graph, neighbor, goal, path)
            for newpath in newpaths:
                paths.append(newpath)
    return paths

def main():
    # Replace 'YOUR_API_KEY' with your actual API key from ExchangeRate-API or any other service.
    api_key = '800ff473a60b029c0f1424ca'
    exchange_rates = get_exchange_rates(api_key)
    # print(exchange_rates)

    # Define a realistic set of available currency pairs
    available_pairs = {
        'USD': ['EUR', 'JPY',  'CNY', 'AUD'],
        'EUR': ['GBP', 'AUD', 'CNY'],
        'JPY': ['USD', 'EUR', 'CNY', 'GBP'],
        'GBP': ['USD', 'EUR', 'CHF', 'JPY', 'CAD', 'AUD'],
        'CHF': ['EUR', 'GBP', 'USD', 'CAD', 'AUD'],
        'CAD': ['JPY', 'GBP', 'AUD', 'CHF'],
        'AUD': ['EUR', 'CAD', 'GBP', 'CHF', 'CNY'],
        'CNY': ['USD', 'JPY', 'AUD', 'CAD'],
    }

    if exchange_rates:
        graph, conversion_rates = create_graph(exchange_rates, available_pairs)
        while True:
            start_currency = input("Enter the start currency (e.g., USD): ").upper()
            goal_currency = input("Enter the goal currency (e.g., JPY): ").upper()
            if start_currency not in graph or goal_currency not in graph:
                print("Invalid currency entered. Please try again.")
                continue

            came_from, cost_so_far = a_star_search(graph, start_currency, goal_currency, exchange_rates)
            if goal_currency not in came_from:
                print(f"No conversion path found from {start_currency} to {goal_currency}.")
                continue

            path = reconstruct_path(came_from, start_currency, goal_currency)
            print(f"A-STAR || Cheapest conversion path from {start_currency} to {goal_currency}:")
            conversion_amount = 1  # Start with 1 unit of the base currency
            for i in range(len(path) - 1):
                from_currency = path[i]
                to_currency = path[i + 1]
                volatile_rate, tax, total_cost_step = conversion_rates[from_currency][to_currency]
                conversion_amount *= total_cost_step  # Update the conversion amount through each step
                base_rate = exchange_rates['conversion_rates'][to_currency] / exchange_rates['conversion_rates'][from_currency]
                volatility_rate = volatile_rate / base_rate - 1
                print(f"{from_currency} -> {to_currency} (Effective Conversion: {conversion_amount:.6f}, Base Rate: {base_rate:.6f}, Volatility: {volatility_rate * 100:.2f}%, Tax: {tax:.2%})")
            print(f"Total effective conversion: {conversion_amount:.6f}\n")

            paths = find_all_paths(graph, start_currency, goal_currency)
            if not paths:
                print(f"No conversion path found from {start_currency} to {goal_currency}.")
            else:
                path_costs = []
                for path in paths:
                    conversion_amount = 1
                    path_details = []
                    for i in range(len(path) - 1):
                        from_currency = path[i]
                        to_currency = path[i + 1]
                        volatile_rate, tax, total_cost_step = conversion_rates[from_currency][to_currency]
                        conversion_amount *= total_cost_step 
                        
                        base_rate = exchange_rates['conversion_rates'][to_currency] / exchange_rates['conversion_rates'][from_currency]
                        volatility_rate = volatile_rate / base_rate - 1 
                        path_details.append((from_currency, to_currency, total_cost_step, volatile_rate, tax, volatility_rate))
                    path_costs.append((conversion_amount, path_details)) 

                # Sort paths by the conversion amount (higher is better)
                path_costs.sort(key=lambda x: x[0], reverse=True)  # Reverse sort to prioritize higher conversion rates

                # Display all paths sorted by total effective conversion
                print(f"All possible paths from {start_currency} to {goal_currency}:")
                for conversion_amount, details in path_costs:
                    print(f"Path starts with 1 {start_currency} converting through:")
                    for from_currency, to_currency, total_cost_step, volatile_rate, tax, volatility_rate in details:
                        print(f"{from_currency} -> {to_currency} (Effective Conversion: {total_cost_step:.6f}, Base Rate: {base_rate:.6f}, Volatility: {volatility_rate * 100:.2f}%, Tax: {tax:.2%})")
                    print(f"Total effective conversion: {conversion_amount:.6f} {goal_currency} from 1 {start_currency}\n")

                validation = False
                while not validation:
                    another = input("Do you want to find another conversion path? (yes/no): ").lower()
                    if another == 'yes':
                        validation = True
                    if another == 'no':
                        break
    else:
        print("Failed to retrieve exchange rates.")

if __name__ == "__main__":
    main()