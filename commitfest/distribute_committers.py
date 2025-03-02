import json

def main():
    pass

if __name__ == '__main__':
    with open('extended_predictions.json', 'r') as f:
        data = json.load(f)

    predictions = data["predictions"]

    base_rates = data["base_rates"]

    print(base_rates)

    print(list(predictions.items())[0])