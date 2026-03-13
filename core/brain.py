def smart_irrigation_decision(crop, temperature, soil, rain):

    ideal = crop.ideal_moisture
    base_water = crop.water_required_per_day

    # Soil deficiency factor
    moisture_gap = ideal - soil

    if moisture_gap <= 0:
        soil_factor = 0.3
    elif moisture_gap < 10:
        soil_factor = 0.7
    else:
        soil_factor = 1.2

    # Temperature impact
    if temperature > 35:
        temp_factor = 1.3
    elif temperature > 30:
        temp_factor = 1.1
    else:
        temp_factor = 1.0

    # Rain impact
    rain_factor = 0 if rain == "yes" else 1

    # Final water calculation
    water_needed = base_water * soil_factor * temp_factor * rain_factor

    # Safety cap (avoid over irrigation)
    if water_needed > base_water * 1.5:
        water_needed = base_water * 1.5

    # Recommendation logic
    if rain == "yes":
        recommendation = "Rain expected. Irrigation skipped to conserve water."
    elif water_needed < base_water * 0.5:
        recommendation = "Minimal irrigation required."
    elif water_needed < base_water:
        recommendation = "Moderate irrigation suggested."
    else:
        recommendation = "High irrigation required due to stress conditions."

    return round(water_needed, 2), recommendation