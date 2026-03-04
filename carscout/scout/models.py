from django.db import models
from django.core.validators import MinValueValidator,MaxValueValidator
from core.models import User
from django.core.exceptions import ValidationError
# Create your models here.


class Vehicle(models.Model):
    vin=models.CharField(max_length=17,unique=True)
    model=models.CharField(max_length=50)
    company=models.CharField(max_length=50)
    year=models.IntegerField()
    FuelType=models.CharField(max_length=50)
    
    
    class Meta:
        db_table='vehicle'
        verbose_name='vehicle'
        verbose_name_plural='vehicle'
    def __str__(self):
        return self.model

class Listing(models.Model):
    STATUS_CHOICES = [
    ('sold', 'Sold'),
    ('available', 'Available'),
]
    seller=models.ForeignKey(User,on_delete=models.CASCADE,)
    vehicle=models.ForeignKey(Vehicle,on_delete=models.CASCADE)
    price=models.DecimalField(max_digits=10, decimal_places=2)
    image=models.ImageField(upload_to='listing_images')
    status=models.CharField(max_length=50,choices=STATUS_CHOICES,default='available')


    def clean(self):
        if hasattr(self, 'seller_id') and self.seller_id is not None:
            if self.seller.role.lower() != 'seller':
                raise ValidationError("Only sellers can create listings")   
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        db_table='listing'
        verbose_name='listing'
        verbose_name_plural='listing'
    def __str__(self):
        return self.vehicle.model

class InspectionReport(models.Model):
    listing=models.ForeignKey(Listing,on_delete=models.CASCADE)
    score=models.DecimalField(max_digits=4, decimal_places=1,
    validators=[MinValueValidator(0.0),MaxValueValidator(10.0)])
    ai_summary=models.TextField()
    accidents_history=models.IntegerField()
    generated_at=models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table='inspection_report'
        verbose_name='inspection_report'
        verbose_name_plural='inspection_report'
    def __str__(self):
        return self.listing.vehicle.model


class Offer(models.Model):
    STATUS_CHOICES = [
    ('accepted', 'Accepted'),
    ('rejected', 'Rejected'),
    ('pending', 'Pending'),
]
    listing=models.ForeignKey(Listing,on_delete=models.CASCADE)
    buyer=models.ForeignKey(User,on_delete=models.CASCADE)
    amount=models.DecimalField(max_digits=10, decimal_places=2)
    status=models.CharField(max_length=50,choices=STATUS_CHOICES,default='pending')
    comment=models.TextField(null=True)

    def clean(self):
        if hasattr(self, 'buyer_id') and self.buyer_id is not None:
            if self.buyer.role.lower() != 'buyer':
                raise ValidationError("Only buyers can make offers")   
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    class Meta:
        db_table='offer'
        verbose_name='offer'
        verbose_name_plural='offer'
    def __str__(self):
        return self.listing.vehicle.model

class TestDrive(models.Model):
    STATUS_CHOICES = [
    ('completed', 'Completed'),
    ('pending', 'Pending'),
    ('cancelled', 'Cancelled'),
]
    buyer=models.ForeignKey(User,on_delete=models.CASCADE)
    listing=models.ForeignKey(Listing,on_delete=models.CASCADE)
    schedule_date=models.DateTimeField()
    location=models.CharField(max_length=100)
    status=models.CharField(max_length=50,choices=STATUS_CHOICES,default='pending')

    class Meta:
        db_table='testdrive'
        verbose_name='testdrive'
        verbose_name_plural='testdrive'
    def __str__(self):
        return self.listing.vehicle.model

class Transaction(models.Model):
    STATUS_CHOICES = [
    ('completed', 'Completed'),
    ('pending', 'Pending'),
    ('failed', 'Failed'),
]
    buyer=models.ForeignKey(User,on_delete=models.PROTECT)
    listing=models.ForeignKey(Listing,on_delete=models.PROTECT)
    amount=models.DecimalField(max_digits=10,decimal_places=2)
    method=models.CharField(max_length=50)
    status=models.CharField(max_length=50,choices=STATUS_CHOICES,default='pending')
    date=models.DateField(auto_now_add=True)

    class Meta:
        db_table='transaction'
        verbose_name='transaction'
        verbose_name_plural='transaction'

    def __str__(self):
        return self.listing.vehicle.model

