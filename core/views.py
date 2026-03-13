from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db.models.functions import TruncDate
from django.db.models import Sum
from datetime import date
import random  # For ±5% variation
import json   # Needed for chart JSON

from .models import FarmerProfile, Crop, IrrigationRecord, WaterUsageLog
from .brain import smart_irrigation_decision

# -------------------
# Authentication
# -------------------
def farmer_login(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid credentials")
    return render(request, "login.html")


def farmer_logout(request):
    logout(request)
    return redirect('login')


# -------------------
# Automated Irrigation
# -------------------
def automate_irrigation(request):
    if request.method == "POST":
        farmer = request.user.farmerprofile
        crop_id = request.POST.get("crop")
        selected_crop = get_object_or_404(Crop, id=crop_id) if crop_id else None

        temperature = float(request.POST.get("temperature", 25))
        soil = float(request.POST.get("soil", 50))
        rain = request.POST.get("rain", "no")

        # AI/automation logic
        automated_water, automated_recommendation = smart_irrigation_decision(selected_crop, temperature, soil, rain)

        # Save in session for dashboard display
        request.session['automated_water'] = automated_water
        request.session['automated_recommendation'] = automated_recommendation

        # Save automated irrigation record
        IrrigationRecord.objects.create(
            farmer=farmer,
            crop=selected_crop,
            soil_moisture=soil,
            temperature=temperature,
            rainfall_expected=(rain=="yes"),
            water_suggested=automated_water,
            recommendation=automated_recommendation,
            automated=True
        )

        # Save Water & Energy Log with ±5% variation
        variation = random.uniform(-0.05, 0.05)
        actual_water = round(automated_water * (1 + variation), 2)

        WaterUsageLog.objects.create(
            farmer=farmer,
            predicted_water_liters=automated_water,
            actual_water_liters=actual_water
        )

        messages.success(request, "Automated irrigation calculated!")

    return redirect('dashboard')


# -------------------
# Dashboard
# -------------------
@login_required
def dashboard(request):
    all_farmers = FarmerProfile.objects.all()
    selected_farmer = request.user.farmerprofile
    selected_crop = None
    temperature = None
    soil = None
    rain = None
    water_needed = None
    recommendation = None

    # -------------------
    # Handle manual prediction
    # -------------------
    if request.method == "POST" and "crop" in request.POST:
        crop_id = request.POST.get("crop")
        selected_crop = get_object_or_404(Crop, id=crop_id)
        
        # Use farmer selection from dropdown
        farmer_id = request.POST.get("farmer")
        if farmer_id:
            selected_farmer = get_object_or_404(FarmerProfile, id=farmer_id)
        else:
            selected_farmer = request.user.farmerprofile  # fallback

        rain = request.POST.get("rain", "no")

        try:
            temperature = float(request.POST.get("temperature"))
            soil = float(request.POST.get("soil"))
        except (TypeError, ValueError):
            messages.error(request, "Invalid temperature or soil value.")
            return redirect('dashboard')

        # AI Prediction
        water_needed, recommendation = smart_irrigation_decision(selected_crop, temperature, soil, rain)

        # Save manual irrigation record
        IrrigationRecord.objects.create(
            farmer=selected_farmer,
            crop=selected_crop,
            soil_moisture=soil,
            temperature=temperature,
            rainfall_expected=(rain=="yes"),
            water_suggested=water_needed,
            recommendation=recommendation,
            automated=False
        )

        # Save Water & Energy Log with ±5% variation
        variation = random.uniform(-0.05, 0.05)
        actual_water = round(water_needed * (1 + variation), 2)

        WaterUsageLog.objects.create(
            farmer=selected_farmer,
            predicted_water_liters=water_needed,
            actual_water_liters=actual_water
        )

    # -------------------
    # Fetch records for dashboard display
    # -------------------
    records = IrrigationRecord.objects.filter(farmer=selected_farmer).order_by("-created_at")
    logs = WaterUsageLog.objects.filter(farmer=selected_farmer).order_by('-created_at')

    total_water = sum(record.water_suggested for record in records)
    total_water_saved = sum(log.water_saved_liters or 0 for log in logs)
    total_energy = sum(log.energy_consumed_kwh or 0 for log in logs)

    # -------------------
    # Chart data (water over time)
    # -------------------
    daily_logs = (
        WaterUsageLog.objects
        .filter(farmer=selected_farmer, created_at__isnull=False)
        .annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(
            predicted=Sum("predicted_water_liters"),
            actual=Sum("actual_water_liters")
        )
        .order_by("day")
    )

    chart_dates_json = json.dumps([
        item["day"].strftime("%d %b") if item["day"] else ""
        for item in daily_logs
    ])
    chart_predicted_json = json.dumps([float(item["predicted"] or 0) for item in daily_logs])
    chart_actual_json = json.dumps([float(item["actual"] or 0) for item in daily_logs])

    # -------------------
    # Rural Water Distribution Module (All farmers today)
    # -------------------
    total_village_water = 100.0  # Example total water available in liters

    today_records = IrrigationRecord.objects.filter(
        created_at__date=date.today()
    ).order_by('farmer__user__username')

    # Fallback: if no records today, show last 5 records
    if not today_records.exists():
        today_records = IrrigationRecord.objects.all().order_by('-created_at')[:5]

    total_requested = sum(record.water_suggested for record in today_records)

    water_distribution = []
    for record in today_records:
        if total_requested <= total_village_water:
            allocated = record.water_suggested
            status = "OK"
        else:
            allocated = round(record.water_suggested * total_village_water / total_requested, 2)
            status = "Reduced"

        water_distribution.append({
            "farmer": record.farmer.user.username,
            "crop": record.crop.crop_name,
            "ai_suggested": record.water_suggested,
            "allocated": allocated,
            "status": status
        })

    # -------------------
    # Pop automated irrigation session
    # -------------------
    automated_water = request.session.pop('automated_water', None)
    automated_recommendation = request.session.pop('automated_recommendation', None)

    # -------------------
    # Context
    # -------------------
    context = {
        "farmers": all_farmers,
        "selected_farmer": selected_farmer,
        "crops": Crop.objects.all(),
        "selected_crop": selected_crop,
        "temperature": temperature,
        "soil": soil,
        "rain": rain,
        "water_needed": water_needed,
        "recommendation": recommendation,
        "records": records,
        "logs": logs,
        "total_water": total_water,
        "total_water_saved": total_water_saved,
        "total_energy": total_energy,
        "chart_dates_json": chart_dates_json,       # Dates for chart
        "chart_predicted_json": chart_predicted_json, # Predicted water
        "chart_actual_json": chart_actual_json,       # Actual water
        "automated_water": automated_water,
        "automated_recommendation": automated_recommendation,
        "water_distribution": water_distribution,
        "total_village_water": total_village_water,
    }

    return render(request, "dashboard.html", context)