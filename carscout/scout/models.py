from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from core.models import User


# ─────────────────────────────────────────
# VEHICLE
# Base vehicle info, separate from listing
# so same car can have multiple listings
# ─────────────────────────────────────────
class Vehicle(models.Model):
    FUEL_CHOICES = [
        ('petrol', 'Petrol'),
        ('diesel', 'Diesel'),
        ('electric', 'Electric'),
        ('hybrid', 'Hybrid'),
    ]
    TRANSMISSION_CHOICES = [
        ('automatic', 'Automatic'),
        ('manual', 'Manual'),
    ]
    CONDITION_CHOICES = [
        ('new', 'New'),
        ('used', 'Used'),
        ('certified', 'Certified Pre-Owned'),
    ]

    vin             = models.CharField(max_length=17, unique=True)
    company         = models.CharField(max_length=100)
    model           = models.CharField(max_length=100)
    year            = models.IntegerField()
    fuel_type       = models.CharField(max_length=20, choices=FUEL_CHOICES, default='petrol')
    transmission    = models.CharField(max_length=20, choices=TRANSMISSION_CHOICES, default='automatic')
    condition       = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='used')
    mileage         = models.IntegerField(default=0)                      # in km
    color           = models.CharField(max_length=50, default='')
    engine_size     = models.CharField(max_length=20, default='')         # e.g. "3.0L", "2000cc"
    num_doors       = models.IntegerField(default=4)
    seating_capacity= models.IntegerField(default=5)
    description     = models.TextField(default='')                        # seller describes condition
    modifications   = models.TextField(default='')                        # any mods done to car

    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'vehicle'
        verbose_name = 'Vehicle'
        verbose_name_plural = 'Vehicles'

    def __str__(self):
        return f"{self.year} {self.company} {self.model}"


# ─────────────────────────────────────────
# LISTING
# A seller posts a vehicle for sale
# ─────────────────────────────────────────
class Listing(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),          # just submitted, waiting for AI inspection
        ('pending_review','Pending Review'), #after ai_scaning line 
        ('ai_scanning', 'AI Scanning'),  # gemini is analyzing it
        ('live', 'Live'),                # approved and visible to buyers
        ('sold', 'Sold'),                # transaction completed
        ('rejected', 'Rejected'),        # admin rejected it
        ('unavailable', 'Unavailable'),  # seller pulled it off
    ]

    seller          = models.ForeignKey(User, on_delete=models.CASCADE, related_name='listings')
    vehicle         = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='listings')
    price           = models.DecimalField(max_digits=12, decimal_places=2)
    image           = models.ImageField(upload_to='listing_images/', null=True, blank=True)
    status          = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_featured     = models.BooleanField(default=False)                  # admin can feature a listing
    views_count     = models.IntegerField(default=0)                      # track how many buyers viewed
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    def clean(self):
        if hasattr(self, 'seller_id') and self.seller_id is not None:
            if self.seller.role.lower() != 'seller':
                raise ValidationError("Only sellers can create listings")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'listing'
        verbose_name = 'Listing'
        verbose_name_plural = 'Listings'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.vehicle} — ${self.price}"


# ─────────────────────────────────────────
# INSPECTION REPORT
# Gemini AI generates this from vehicle
# description, accident history, service
# history — no images needed
# ─────────────────────────────────────────
class InspectionReport(models.Model):
    ACCIDENT_CHOICES = [
        ('none', 'No Accidents'),
        ('minor', 'Minor Accident'),
        ('major', 'Major Accident'),
        ('unknown', 'Unknown'),
    ]
    RECOMMENDATION_CHOICES = [
        ('buy_confident', 'Buy with Confidence'),
        ('negotiate', 'Negotiate Price'),
        ('inspect_further', 'Request Full Inspection'),
        ('avoid', 'Avoid'),
    ]
    RISK_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    listing             = models.OneToOneField(Listing, on_delete=models.CASCADE, related_name='inspection')
    
    # Input data Gemini reads
    accident_history    = models.CharField(max_length=20, choices=ACCIDENT_CHOICES, default='none')
    accident_details    = models.TextField(default='')        # seller describes what happened
    service_history     = models.TextField(default='')        # maintenance records description
    previous_owners     = models.IntegerField(default=0)

    # AI Outputs
    score               = models.DecimalField(
                            max_digits=3, decimal_places=1,
                            validators=[MinValueValidator(0.0), MaxValueValidator(10.0)],
                            null=True, blank=True
                          )
    overall_condition   = models.CharField(max_length=20, default='', blank=True)  # Excellent/Good/Fair/Poor
    ai_summary          = models.TextField(default='', blank=True)                 # main review paragraph
    risk_level          = models.CharField(max_length=10, choices=RISK_CHOICES, default='low', blank=True)
    recommendation      = models.CharField(max_length=20, choices=RECOMMENDATION_CHOICES, default='negotiate', blank=True)
    
    # Detailed breakdown stored as JSON
    issues_detected     = models.JSONField(default=list, blank=True)   # ["rust on door", "worn tyres"]
    positives           = models.JSONField(default=list, blank=True)   # ["full service history"]
    buyer_tips          = models.JSONField(default=list, blank=True)   # ["ask for full service records"]
    
    # Sub-scores
    mileage_assessment  = models.TextField(default='', blank=True)
    price_assessment    = models.TextField(default='', blank=True)
    accident_impact     = models.TextField(default='', blank=True)

    generated_at        = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'inspection_report'
        verbose_name = 'Inspection Report'
        verbose_name_plural = 'Inspection Reports'

    def __str__(self):
        return f"Report — {self.listing.vehicle} (Score: {self.score})"


# ─────────────────────────────────────────
# OFFER
# Buyer makes an offer on a listing
# ─────────────────────────────────────────
class Offer(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('countered', 'Countered'),      # seller can counter the offer
        ('withdrawn', 'Withdrawn'),      # buyer withdrew the offer
    ]

    listing         = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='offers')
    buyer           = models.ForeignKey(User, on_delete=models.CASCADE, related_name='offers')
    amount          = models.DecimalField(max_digits=12, decimal_places=2)
    status          = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    comment         = models.TextField(default='', blank=True)            # buyer message with offer
    counter_amount  = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)  # seller counter
    counter_comment = models.TextField(default='', blank=True)            # seller counter message
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    def clean(self):
        if hasattr(self, 'buyer_id') and self.buyer_id is not None:
            if self.buyer.role.lower() != 'buyer':
                raise ValidationError("Only buyers can make offers")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'offer'
        verbose_name = 'Offer'
        verbose_name_plural = 'Offers'
        ordering = ['-created_at']

    def __str__(self):
        return f"Offer ${self.amount} on {self.listing.vehicle} — {self.status}"


# ─────────────────────────────────────────
# MESSAGE
# In-app messaging between buyer and seller
# ─────────────────────────────────────────
class Message(models.Model):
    listing         = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='messages')
    sender          = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    body            = models.TextField()
    is_read         = models.BooleanField(default=False)
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'message'
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender} → {self.receiver} on {self.listing.vehicle}"


# ─────────────────────────────────────────
# TEST DRIVE
# Buyer schedules a test drive for a listing
# ─────────────────────────────────────────
class TestDrive(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    listing         = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='test_drives')
    buyer           = models.ForeignKey(User, on_delete=models.CASCADE, related_name='test_drives')
    scheduled_date  = models.DateTimeField()
    location        = models.CharField(max_length=255, default='')
    status          = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes           = models.TextField(default='', blank=True)            # any special requests
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'testdrive'
        verbose_name = 'Test Drive'
        verbose_name_plural = 'Test Drives'
        ordering = ['scheduled_date']

    def __str__(self):
        return f"Test Drive — {self.listing.vehicle} by {self.buyer}"


# ─────────────────────────────────────────
# TRANSACTION
# Final payment when offer is accepted
# ─────────────────────────────────────────
class Transaction(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    METHOD_CHOICES = [
        ('bank_transfer', 'Bank Transfer'),
        ('cash', 'Cash'),
        ('finance', 'Finance/Loan'),
        ('online', 'Online Payment'),
    ]

    listing         = models.ForeignKey(Listing, on_delete=models.PROTECT, related_name='transactions')
    buyer           = models.ForeignKey(User, on_delete=models.PROTECT, related_name='transactions')
    offer           = models.OneToOneField(Offer, on_delete=models.PROTECT, related_name='transaction', null=True, blank=True)
    amount          = models.DecimalField(max_digits=12, decimal_places=2)
    method          = models.CharField(max_length=20, choices=METHOD_CHOICES, default='bank_transfer')
    status          = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reference_number= models.CharField(max_length=100, default='', blank=True)  # payment ref
    notes           = models.TextField(default='', blank=True)
    date            = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'transaction'
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'
        ordering = ['-date']

    def __str__(self):
        return f"Transaction ${self.amount} — {self.listing.vehicle} — {self.status}"


# ─────────────────────────────────────────
# PRICE ALERT
# Buyer sets an alert for a price drop
# ─────────────────────────────────────────
class PriceAlert(models.Model):
    buyer           = models.ForeignKey(User, on_delete=models.CASCADE, related_name='price_alerts')
    listing         = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='price_alerts')
    target_price    = models.DecimalField(max_digits=12, decimal_places=2)
    is_triggered    = models.BooleanField(default=False)
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'price_alert'
        verbose_name = 'Price Alert'
        verbose_name_plural = 'Price Alerts'

    def __str__(self):
        return f"Alert — {self.buyer} wants {self.listing.vehicle} under ${self.target_price}"


# ─────────────────────────────────────────
# WISHLIST
# Buyer saves listings they like
# ─────────────────────────────────────────
class Wishlist(models.Model):
    buyer           = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlist')
    listing         = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='wishlisted_by')
    added_at        = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'wishlist'
        verbose_name = 'Wishlist'
        verbose_name_plural = 'Wishlist'
        unique_together = ('buyer', 'listing')   # cant save same listing twice

    def __str__(self):
        return f"{self.buyer} saved {self.listing.vehicle}"