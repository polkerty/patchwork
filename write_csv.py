import csv

def dict_to_csv(data: dict, filename: str):
    """
    Converts a dictionary of dictionaries to a CSV file.

    Parameters:
    - data (dict): The input dictionary of dictionaries.
    - filename (str): The name of the output CSV file.

    The outer dictionary keys become the "ID" column,
    and the inner dictionary keys become the CSV headers.
    """
    if not data:
        raise ValueError("Input dictionary is empty.")

    # Determine column headers
    fieldnames = ["ID"] + list(next(iter(data.values())).keys())

    # Write to CSV
    with open(filename, mode="w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for key, values in data.items():
            writer.writerow({"ID": key, **values})

    print(f"CSV file '{filename}' created successfully.")
