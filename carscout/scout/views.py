from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from scout.decorators import role_required
from scout.models import Listing, Vehicle, InspectionReport, Wishlist, Offer, Message
from scout.forms import VehicleForm, ListingForm, InspectionInputForm, MakeOfferForm, CounterOfferForm
from scout.gemini_service import run_ai_inspection
from django.db.models import Q


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
    wishlist_ids = Wishlist.objects.filter(buyer=request.user).values_list('listing_id', flat=True)
    wishlist_listings = Listing.objects.filter(
        id__in=wishlist_ids, status='live'
    ).select_related('vehicle', 'inspection').order_by('-wishlisted_by__added_at')

    recent_listings = Listing.objects.filter(
        status='live'
    ).select_related('vehicle', 'inspection').order_by('-created_at')[:6]

    context = {
        'wishlist_listings': wishlist_listings,
        'recent_listings': recent_listings,
        'wishlist_count': wishlist_ids.count(),
    }
    return render(request, 'Scout/Buyer/buyer_dashboard.html', context)


@role_required(allowed_roles=['Buyer'])
def BrowseListingsView(request):
    listings = Listing.objects.filter(status='live').select_related('vehicle', 'inspection').order_by('-created_at')

    # --- filters ---
    q = request.GET.get('q', '').strip()
    fuel = request.GET.get('fuel', '')
    transmission = request.GET.get('transmission', '')
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    condition = request.GET.get('condition', '')

    if q:
        listings = listings.filter(
            Q(vehicle__company__icontains=q) |
            Q(vehicle__model__icontains=q) |
            Q(vehicle__vin__icontains=q)
        )
    if fuel:
        listings = listings.filter(vehicle__fuel_type=fuel)
    if transmission:
        listings = listings.filter(vehicle__transmission=transmission)
    if condition:
        listings = listings.filter(vehicle__condition=condition)
    if min_price:
        listings = listings.filter(price__gte=min_price)
    if max_price:
        listings = listings.filter(price__lte=max_price)

    wishlist_ids = list(
        Wishlist.objects.filter(buyer=request.user).values_list('listing_id', flat=True)
    )

    context = {
                'listings': listings,
                'wishlist_ids': wishlist_ids,
                'total': listings.count(),
                # flat variables instead of nested dict
                'filter_q': q,
                'filter_fuel': fuel,
                'filter_transmission': transmission,
                'filter_condition': condition,
                'filter_min_price': min_price,
                'filter_max_price': max_price,
              }
    return render(request, 'Scout/Buyer/browse_listings.html', context)


@role_required(allowed_roles=['Buyer'])
def BuyerListingDetailView(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id, status='live')
    listing.views_count += 1
    listing.save(update_fields=['views_count'])

    inspection = getattr(listing, 'inspection', None)
    in_wishlist = Wishlist.objects.filter(buyer=request.user, listing=listing).exists()

    context = {
        'listing': listing,
        'inspection': inspection,
        'in_wishlist': in_wishlist,
    }
    return render(request, 'Scout/Buyer/listing_detail.html', context)


@role_required(allowed_roles=['Buyer'])
def ToggleWishlistView(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id, status='live')
    obj, created = Wishlist.objects.get_or_create(buyer=request.user, listing=listing)
    if not created:
        obj.delete()
    # redirect back to wherever the user came from
    next_url = request.GET.get('next') or request.META.get('HTTP_REFERER') or 'browse_listings'
    from django.shortcuts import redirect as _redirect
    return _redirect(next_url)

# ── BUYER: Make an offer on a listing ────────────────────────────────────────
@role_required(allowed_roles=['Buyer'])
def MakeOfferView(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id, status='live')

    # prevent buyer from offering on their own listing (edge case)
    existing_offer = Offer.objects.filter(listing=listing, buyer=request.user).exclude(status='withdrawn').first()

    if request.method == 'POST':
        form = MakeOfferForm(request.POST)
        if form.is_valid():
            offer = form.save(commit=False)
            offer.listing = listing
            offer.buyer = request.user
            offer.status = 'pending'
            offer.save()
            return redirect('buyer_offers')
    else:
        form = MakeOfferForm()

    context = {
        'listing': listing,
        'form': form,
        'existing_offer': existing_offer,
    }
    return render(request, 'Scout/Buyer/make_offer.html', context)


# ── BUYER: View all my offers ─────────────────────────────────────────────────
@role_required(allowed_roles=['Buyer'])
def BuyerOffersView(request):
    offers = Offer.objects.filter(buyer=request.user).select_related('listing', 'listing__vehicle').order_by('-created_at')
    context = {'offers': offers}
    return render(request, 'Scout/Buyer/my_offers.html', context)


# ── BUYER: Accept a counter offer ────────────────────────────────────────────
@role_required(allowed_roles=['Buyer'])
def AcceptCounterView(request, offer_id):
    offer = get_object_or_404(Offer, id=offer_id, buyer=request.user, status='countered')
    if request.method == 'POST':
        offer.status = 'accepted'
        offer.amount = offer.counter_amount   # finalise at counter price
        offer.save()
    return redirect('buyer_offers')


# ── BUYER: Withdraw an offer ──────────────────────────────────────────────────
@role_required(allowed_roles=['Buyer'])
def WithdrawOfferView(request, offer_id):
    offer = get_object_or_404(Offer, id=offer_id, buyer=request.user)
    if request.method == 'POST':
        offer.status = 'withdrawn'
        offer.save()
    return redirect('buyer_offers')


# ── SELLER: View all offers on their listings ─────────────────────────────────
@role_required(allowed_roles=['Seller'])
def SellerOffersView(request):
    offers = Offer.objects.filter(
        listing__seller=request.user
    ).select_related('listing', 'listing__vehicle', 'buyer').order_by('-created_at')

    pending_count = offers.filter(status='pending').count()
    context = {
        'offers': offers,
        'pending_count': pending_count,
    }
    return render(request, 'Scout/Seller/offers.html', context)


# ── SELLER: Accept an offer ───────────────────────────────────────────────────
@role_required(allowed_roles=['Seller'])
def AcceptOfferView(request, offer_id):
    offer = get_object_or_404(Offer, id=offer_id, listing__seller=request.user)
    if request.method == 'POST':
        offer.status = 'accepted'
        offer.save()
        # reject all other pending offers on the same listing
        Offer.objects.filter(listing=offer.listing, status='pending').exclude(id=offer.id).update(status='rejected')
    return redirect('seller_offers')


# ── SELLER: Reject an offer ───────────────────────────────────────────────────
@role_required(allowed_roles=['Seller'])
def RejectOfferView(request, offer_id):
    offer = get_object_or_404(Offer, id=offer_id, listing__seller=request.user)
    if request.method == 'POST':
        offer.status = 'rejected'
        offer.save()
    return redirect('seller_offers')


# ── SELLER: Counter an offer ──────────────────────────────────────────────────
@role_required(allowed_roles=['Seller'])
def CounterOfferView(request, offer_id):
    offer = get_object_or_404(Offer, id=offer_id, listing__seller=request.user, status='pending')
    if request.method == 'POST':
        form = CounterOfferForm(request.POST, instance=offer)
        if form.is_valid():
            offer = form.save(commit=False)
            offer.status = 'countered'
            offer.save()
            return redirect('seller_offers')
    else:
        form = CounterOfferForm(instance=offer)

    context = {'form': form, 'offer': offer}
    return render(request, 'Scout/Seller/counter_offer.html', context)


# ── BUYER: View inbox (all conversations) ────────────────────────────────────
@role_required(allowed_roles=['Buyer'])
def BuyerInboxView(request):
    # Get all listings this buyer has messaged on
    from django.db.models import Max, OuterRef, Subquery
    conversations = Message.objects.filter(
        sender=request.user
    ).values('listing').union(
        Message.objects.filter(receiver=request.user).values('listing')
    )
    listing_ids = [c['listing'] for c in conversations]
    listings = Listing.objects.filter(id__in=listing_ids).select_related('vehicle', 'seller')

    # Attach last message + unread count to each listing
    inbox = []
    for listing in listings:
        last_msg = Message.objects.filter(listing=listing).order_by('-created_at').first()
        unread = Message.objects.filter(listing=listing, receiver=request.user, is_read=False).count()
        inbox.append({'listing': listing, 'last_msg': last_msg, 'unread': unread})

    context = {'inbox': inbox}
    return render(request, 'Scout/Buyer/inbox.html', context)


# ── BUYER: Chat with seller on a specific listing ─────────────────────────────
@role_required(allowed_roles=['Buyer'])
def BuyerChatView(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id)
    seller = listing.seller

    # Mark all messages from seller as read
    Message.objects.filter(listing=listing, sender=seller, receiver=request.user, is_read=False).update(is_read=True)

    messages = Message.objects.filter(listing=listing).filter(
        sender__in=[request.user, seller],
        receiver__in=[request.user, seller]
    ).order_by('created_at')

    if request.method == 'POST':
        body = request.POST.get('body', '').strip()
        if body:
            Message.objects.create(
                listing=listing,
                sender=request.user,
                receiver=seller,
                body=body,
            )
        return redirect('buyer_chat', listing_id=listing_id)

    context = {
        'listing': listing,
        'messages': messages,
        'other_user': seller,
    }
    return render(request, 'Scout/Buyer/chat.html', context)


# ── SELLER: View inbox (all conversations across all listings) ────────────────
@role_required(allowed_roles=['Seller'])
def SellerInboxView(request):
    # Find all unique (listing, buyer) pairs that have messages
    from django.db.models import Count
    sent = Message.objects.filter(sender=request.user).values_list('listing_id', 'receiver_id')
    received = Message.objects.filter(receiver=request.user).values_list('listing_id', 'sender_id')

    pairs = set()
    for listing_id, other_id in sent:
        pairs.add((listing_id, other_id))
    for listing_id, other_id in received:
        pairs.add((listing_id, other_id))

    from core.models import User
    inbox = []
    for listing_id, buyer_id in pairs:
        try:
            listing = Listing.objects.select_related('vehicle').get(id=listing_id)
            buyer = User.objects.get(id=buyer_id)
            last_msg = Message.objects.filter(listing=listing, sender__in=[request.user, buyer], receiver__in=[request.user, buyer]).order_by('-created_at').first()
            unread = Message.objects.filter(listing=listing, sender=buyer, receiver=request.user, is_read=False).count()
            inbox.append({'listing': listing, 'buyer': buyer, 'last_msg': last_msg, 'unread': unread})
        except Exception:
            continue

    inbox.sort(key=lambda x: x['last_msg'].created_at if x['last_msg'] else 0, reverse=True)
    context = {'inbox': inbox}
    return render(request, 'Scout/Seller/inbox.html', context)


# ── SELLER: Chat with a specific buyer on a listing ───────────────────────────
@role_required(allowed_roles=['Seller'])
def SellerChatView(request, listing_id, buyer_id):
    listing = get_object_or_404(Listing, id=listing_id, seller=request.user)
    from core.models import User
    buyer = get_object_or_404(User, id=buyer_id, role='Buyer')

    # Mark all messages from buyer as read
    Message.objects.filter(listing=listing, sender=buyer, receiver=request.user, is_read=False).update(is_read=True)

    messages = Message.objects.filter(listing=listing).filter(
        sender__in=[request.user, buyer],
        receiver__in=[request.user, buyer]
    ).order_by('created_at')

    if request.method == 'POST':
        body = request.POST.get('body', '').strip()
        if body:
            Message.objects.create(
                listing=listing,
                sender=request.user,
                receiver=buyer,
                body=body,
            )
        return redirect('seller_chat', listing_id=listing_id, buyer_id=buyer_id)

    context = {
        'listing': listing,
        'messages': messages,
        'other_user': buyer,
    }
    return render(request, 'Scout/Seller/chat.html', context)