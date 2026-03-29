import pandas as pd
import json

def solve(input_data):
    # Simulate a slow, memory-heavy pipeline
    df = pd.DataFrame(input_data)
    
    # Inefficient apply operation
    def format_price(row):
        return f"${row['price']:.2f}"
    
    df['formatted'] = df.apply(format_price, axis=1)
    
    # Inefficient grouping
    summary = df.groupby('category').agg({'price': 'sum'}).to_dict()['price']
    
    return summary
