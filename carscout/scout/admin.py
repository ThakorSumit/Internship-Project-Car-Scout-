from django.contrib import admin
from .models import Vehicle,Listing,InspectionReport,Offer,TestDrive,Transaction
# Register your models here.

admin.site.register(Vehicle)
admin.site.register(Listing)
admin.site.register(InspectionReport)
admin.site.register(Offer)
admin.site.register(TestDrive)
admin.site.register(Transaction)    
