from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Transaction

@receiver(post_save, sender=Transaction)
def update_listing_status(sender, instance, created, **kwargs):
    # If the transaction is marked as 'completed' 
    if instance.status == 'completed':
        listing = instance.listing
        listing.status = 'sold' # Matches STATUS_CHOICES in Listing [cite: 2]
        listing.save()

