from django.db import models
from django.contrib.auth.models import User

# -------------------------
# Farmer Profile / Login
# -------------------------
class FarmerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    location = models.CharField(max_length=100, help_text="Farmer's location")
    land_size = models.FloatField(help_text="Land size in acres")

    def __str__(self):
        return self.user.username


# -------------------------
# Crop Model
# -------------------------
class Crop(models.Model):
    crop_name = models.CharField(max_length=100, help_text="Name of the crop")
    water_required_per_day = models.FloatField(
        default=0, help_text="Litres of water required per day"
    )
    ideal_moisture = models.FloatField(default=0, help_text="Ideal soil moisture %")

    def __str__(self):
        return self.crop_name


# -------------------------
# Irrigation Record (AI prediction + automated irrigation)
# -------------------------
class IrrigationRecord(models.Model):
    farmer = models.ForeignKey(FarmerProfile, on_delete=models.CASCADE)
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE)
    soil_moisture = models.FloatField(default=0, help_text="Current soil moisture %")
    temperature = models.FloatField(default=0, help_text="Temperature in °C")
    rainfall_expected = models.BooleanField(default=False)
    water_suggested = models.FloatField(default=0, help_text="AI suggested water in litres")
    recommendation = models.TextField(blank=True, help_text="Irrigation recommendation")
    created_at = models.DateTimeField(auto_now_add=True)
    automated = models.BooleanField(default=True, help_text="Was irrigation automated?")

    def __str__(self):
        return f"{self.farmer.user.username} - {self.crop.crop_name} - {self.created_at.strftime('%d %b %Y')}"


# -------------------------
# Water & Energy Optimization Logs
# -------------------------
class WaterUsageLog(models.Model):
    farmer = models.ForeignKey(FarmerProfile, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    predicted_water_liters = models.FloatField(default=0, help_text="AI recommended water")
    actual_water_liters = models.FloatField(default=0, help_text="Actual water used")
    water_saved_liters = models.FloatField(blank=True, null=True)
    energy_consumed_kwh = models.FloatField(blank=True, null=True)

    def save(self, *args, **kwargs):
        # Ensure predicted and actual values are numeric
        predicted = self.predicted_water_liters or 0
        actual = self.actual_water_liters or 0

        # Auto calculate water saved and energy consumed
        self.water_saved_liters = max(predicted - actual, 0)
        self.energy_consumed_kwh = actual * 0.002  # 0.002 kWh per liter

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.farmer.user.username} - {self.created_at.strftime('%d %b %Y %H:%M')} - Water Saved: {self.water_saved_liters:.2f} L"