from django import forms
from .models import Vehicle, Listing, InspectionReport, Offer


class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = [
            'vin', 'company', 'model', 'year', 'fuel_type',
            'transmission', 'condition', 'mileage', 'color',
            'engine_size', 'num_doors', 'seating_capacity',
            'description', 'modifications',
        ]
        widgets = {
            'vin': forms.TextInput(attrs={'placeholder': 'e.g. 1HGBH41JXMN109186'}),
            'company': forms.TextInput(attrs={'placeholder': 'e.g. Porsche'}),
            'model': forms.TextInput(attrs={'placeholder': 'e.g. 911 Carrera S'}),
            'year': forms.NumberInput(attrs={'placeholder': '2022', 'min': 1900, 'max': 2026}),
            'mileage': forms.NumberInput(attrs={'placeholder': '0', 'min': 0}),
            'color': forms.TextInput(attrs={'placeholder': 'e.g. Midnight Blue'}),
            'engine_size': forms.TextInput(attrs={'placeholder': 'e.g. 3.0L Twin-Turbo'}),
            'num_doors': forms.NumberInput(attrs={'min': 2, 'max': 6}),
            'seating_capacity': forms.NumberInput(attrs={'min': 1, 'max': 9}),
            'description': forms.Textarea(attrs={
                'rows': 5,
                'placeholder': 'Describe the vehicle condition, history, and any notable features...'
            }),
            'modifications': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'List any modifications or upgrades (or leave blank)...'
            }),
        }


class ListingForm(forms.ModelForm):
    class Meta:
        model = Listing
        fields = ['price', 'image']
        widgets = {
            'price': forms.NumberInput(attrs={'placeholder': 'e.g. 142000', 'min': 0}),
        }


class InspectionInputForm(forms.ModelForm):
    """Seller-provided inspection info before AI runs."""
    class Meta:
        model = InspectionReport
        fields = [
            'accident_history', 'accident_details',
            'service_history', 'previous_owners',
        ]
        widgets = {
            'accident_details': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Describe any accidents (or leave blank if none)...'
            }),
            'service_history': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'List service records, maintenance history...'
            }),
            'previous_owners': forms.NumberInput(attrs={'min': 1}),
        }


#-------offer------
class MakeOfferForm(forms.ModelForm):
    class Meta:
        model = Offer
        fields = ['amount', 'comment']
        widgets = {
            'amount': forms.NumberInput(attrs={'placeholder': 'Your offer amount'}),
            'comment': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Optional message to the seller...'}),
        }

class CounterOfferForm(forms.ModelForm):
    class Meta:
        model = Offer
        fields = ['counter_amount', 'counter_comment']
        widgets = {
            'counter_amount': forms.NumberInput(attrs={
                'placeholder': 'Your counter amount',
                'style': 'width:100%; background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1); border-radius:9px; padding:11px 14px; font-family:DM Sans,sans-serif; font-size:0.92rem; color:#fff; outline:none; box-sizing:border-box;'
            }),
            'counter_comment': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Message to the buyer...',
                'style': 'width:100%; background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1); border-radius:9px; padding:11px 14px; font-family:DM Sans,sans-serif; font-size:0.92rem; color:#fff; outline:none; box-sizing:border-box; resize:vertical;'
            }),
        }