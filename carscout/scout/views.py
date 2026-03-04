from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from scout.decorators import role_required
from scout.models import Listing, Vehicle, InspectionReport
from scout.forms import VehicleForm, ListingForm, InspectionInputForm
from scout.gemini_service import run_ai_inspection


# ─── Admin ───────────────────────────────────────────────────────────────────

@role_required(allowed_roles=['Admin'])
def AdminDashboardView(request):
    return render(request, 'Scout/Admin/admin_dashboard.html')


# ─── Seller ──────────────────────────────────────────────────────────────────

@role_required(allowed_roles=['Seller'])
def SellerDashboardView(request):
    listings = Listing.objects.filter(seller=request.user).select_related('vehicle', 'inspection').order_by('-created_at')
    context = {
        'listings': listings,
        'total_listings': listings.count(),
        'live_listings': listings.filter(status='live').count(),
        'total_views': sum(l.views_count for l in listings),
    }
    return render(request, 'Scout/Seller/seller_dashboard.html', context)


@role_required(allowed_roles=['Seller'])
def AddListingView(request):
    if request.method == 'POST':
        vehicle_form = VehicleForm(request.POST)
        listing_form = ListingForm(request.POST, request.FILES)
        inspection_form = InspectionInputForm(request.POST)

        if vehicle_form.is_valid() and listing_form.is_valid() and inspection_form.is_valid():
            # Save vehicle
            vehicle = vehicle_form.save()

            # Save listing
            listing = listing_form.save(commit=False)
            listing.seller = request.user
            listing.vehicle = vehicle
            listing.status = 'ai_scanning'
            listing.save()

            # Save inspection inputs from seller
            inspection = inspection_form.save(commit=False)
            inspection.listing = listing
            inspection.save()

            # Kick off AI inspection in background
            run_ai_inspection(listing.id)

            return redirect('seller_listing_detail', listing_id=listing.id)
        else:
            context = {
                'vehicle_form': vehicle_form,
                'listing_form': listing_form,
                'inspection_form': inspection_form,
            }
            return render(request, 'Scout/Seller/add_listing.html', context)

    else:
        context = {
            'vehicle_form': VehicleForm(),
            'listing_form': ListingForm(),
            'inspection_form': InspectionInputForm(),
        }
        return render(request, 'Scout/Seller/add_listing.html', context)


@role_required(allowed_roles=['Seller'])
def SellerListingDetailView(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id, seller=request.user)
    inspection = getattr(listing, 'inspection', None)
    context = {
        'listing': listing,
        'inspection': inspection,
    }
    return render(request, 'Scout/Seller/listing_detail.html', context)


@role_required(allowed_roles=['Seller'])
def DeleteListingView(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id, seller=request.user)
    if request.method == 'POST':
        listing.delete()
        return redirect('seller_dashboard')
    return render(request, 'Scout/Seller/confirm_delete.html', {'listing': listing})


# ─── Buyer ───────────────────────────────────────────────────────────────────

@role_required(allowed_roles=['Buyer'])
def BuyerDashboardView(request):
    return render(request, 'Scout/Buyer/buyer_dashboard.html')