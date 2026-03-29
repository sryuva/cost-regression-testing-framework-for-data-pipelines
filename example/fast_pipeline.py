from collections import defaultdict

def solve(input_data):
    # Optimized dict operations without Pandas
    summary = defaultdict(float)
    
    for row in input_data:
        # Avoid string allocation mapping unless requested natively
        summary[row['category']] += row['price']
        
    return dict(summary)
