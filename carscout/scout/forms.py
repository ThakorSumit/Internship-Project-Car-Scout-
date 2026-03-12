from django import forms
from .models import Vehicle, Listing, InspectionReport, Offer, TestDrive,Transaction,PriceAlert


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
            'previous_owners': forms.NumberInput(attrs={'min': 0}),
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

#-----------------test_drive------------------------------

class TestDriveForm(forms.ModelForm):
    scheduled_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={
            'type': 'datetime-local',
            'class': 'form-control',
        }),
        input_formats=['%Y-%m-%dT%H:%M'],
    )

    class Meta:
        model = TestDrive
        fields = ['scheduled_date', 'location', 'notes']
        widgets = {
            'location': forms.TextInput(attrs={
                'placeholder': 'e.g. Seller\'s address or preferred meetup point',
            }),
            'notes': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Any special requests or questions for the seller...',
            }),
        }

#-----------------transaction------------------------------
class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['method', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Any payment notes or reference details...',
            }),
        }

# ─── Price Alert ────────────────────────────────────────────────────

class PriceAlertForm(forms.ModelForm):
    class Meta:
        model = PriceAlert
        fields = ['target_price']
        widgets = {
            'target_price': forms.NumberInput(attrs={
                'placeholder': 'e.g. 45000',
                'min': 0,
                'step': '100',
                'class': 'alert-price-input',
            })
        }
        labels = {
            'target_price': 'Alert me when price drops to or below ($)'
        }

class EditPriceForm(forms.ModelForm):
   class Meta:
       model = Listing
       fields = ['price']
       widgets = {
            'price': forms.NumberInput(attrs={
                'placeholder': 'e.g. 48000',
                'min': 0,
                'step': '100',
            })
        }
       labels = {
            'price': 'New Asking Price (USD)'
        }