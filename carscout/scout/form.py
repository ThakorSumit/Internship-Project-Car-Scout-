from django import forms
from .models import Vehicle,Listing,TestDrive,Offer,Transaction,InspectionReport

class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = ['vin', 'company', 'model', 'year', 'FuelType']
        widgets = {
            'year': forms.NumberInput(attrs={'min_value': 1900, 'max_value': 2025}),
        }

class listingForm(forms.ModelForm):   
    image = forms.ImageField(required=False)
    class Meta:
        model = Listing
        fields = ['price', 'image']
        widgets = {
            'price': forms.NumberInput(attrs={'min_value': 0}),
        }

class InspectionReportForm(forms.ModelForm):
    class Meta:
        model = InspectionReport
        fields = ['listing', 'score', 'ai_summary','accidents_history']
        widgets = {
            'score': forms.NumberInput(attrs={'min_value': 0, 'max_value': 10}),
        }


class TestDriveForm(forms.ModelForm):
    class Meta:
        model = TestDrive
        fields = ['schedule_date', 'location']
        widgets = {
            'schedule_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'location': forms.TextInput(attrs={'placeholder': 'Enter location'}),
            
        }

class OfferForm(forms.ModelForm):
    class Meta:
        model = Offer
        fields = ['amount', 'comment']
        widgets = {
            'amount': forms.NumberInput(attrs={'min_value': 0}),
        }

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['listing', 'buyer', 'amount','method','status']
        widgets = {
            'amount': forms.NumberInput(attrs={'min_value': 0}),
        }
