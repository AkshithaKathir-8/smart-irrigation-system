from django.contrib import admin
from .models import FarmerProfile , WaterUsageLog, Crop, IrrigationRecord

admin.site.register(FarmerProfile)
admin.site.register(WaterUsageLog)
admin.site.register(Crop)
admin.site.register(IrrigationRecord)