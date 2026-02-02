def calculate_sheet_weight(length_mm, width_mm, gsm):
    """
    Calculate weight of a single sheet.
    Area (sq m) = (Length * Width) / 1,000,000
    Weight (kg) = Area * GSM / 1000
    """
    area_sq_m = (length_mm * width_mm) / 1_000_000
    weight_kg = (area_sq_m * gsm) / 1000
    return weight_kg

def calculate_box_weight(sheet_weight_kg, sheets_per_box):
    """
    Calculate total weight of the box.
    """
    return sheet_weight_kg * sheets_per_box

def calculate_material_cost(sheet_weight_kg, paper_rate_per_kg):
    """
    Calculate material cost based on weight and rate.
    """
    return sheet_weight_kg * paper_rate_per_kg

def calculate_selling_price(total_cost, margin_percent):
    """
    Calculate selling price based on margin percentage.
    SP = Cost / (1 - Margin%)
    """
    if margin_percent >= 100:
        return 0 # Avoid division by zero or negative
    return total_cost / (1 - (margin_percent / 100))
