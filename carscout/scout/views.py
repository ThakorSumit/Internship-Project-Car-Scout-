from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from scout.decorators import role_required
from scout.models import Listing, Vehicle, InspectionReport, Wishlist, Offer, Message, TestDrive, Transaction, PriceAlert
from scout.forms import VehicleForm, ListingForm, InspectionInputForm, MakeOfferForm, CounterOfferForm, TestDriveForm, TransactionForm, PriceAlertForm, EditPriceForm
from scout.gemini_service import run_ai_inspection
from django.db.models import Q
from django.utils import timezone
from django.http import HttpResponseForbidden, Http404, JsonResponse
import uuid
from django.contrib.auth import get_user_model
from django.conf import settings
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Sum
from core.models import User as CoreUser

# ─── Admin ───────────────────────────────────────────────────────────────────

@role_required(allowed_roles=['Admin'])
def AdminDashboardView(request):
    

    # ── Stats ──────────────────────────────────────────────
    total_listings        = Listing.objects.count()
    live_listings         = Listing.objects.filter(status='live').count()
    total_buyers          = CoreUser.objects.filter(role='Buyer').count()
    total_sellers         = CoreUser.objects.filter(role='Seller').count()
    pending_inspections   = InspectionReport.objects.filter(score__isnull=True).count()
    active_offers         = Offer.objects.filter(status='pending').count()
    total_transactions    = Transaction.objects.count()
    total_revenue         = Transaction.objects.aggregate(t=Sum('amount'))['t'] or 0

    # ── Recent Listings (last 10) ───────────────────────────
    recent_listings = Listing.objects.select_related(
        'vehicle', 'seller', 'inspection'
    ).order_by('-created_at')[:10]

    # ── Recent Users (last 8) ───────────────────────────────
    recent_users = CoreUser.objects.exclude(
        role='Admin'
    ).order_by('-created_at')[:8]

    # ── Recent Transactions (last 5) ───────────────────────
    recent_transactions = Transaction.objects.select_related(
        'listing__vehicle', 'buyer'
    ).order_by('-date')[:5]

    # ── Recent Offers ───────────────────────────────────────
    recent_offers = Offer.objects.select_related(
        'listing__vehicle', 'buyer'
    ).order_by('-created_at')[:5]

    context = {
        'total_listings':       total_listings,
        'live_listings':        live_listings,
        'total_buyers':         total_buyers,
        'total_sellers':        total_sellers,
        'pending_inspections':  pending_inspections,
        'active_offers':        active_offers,
        'total_transactions':   total_transactions,
        'total_revenue':        total_revenue,
        'recent_listings':      recent_listings,
        'recent_users':         recent_users,
        'recent_transactions':  recent_transactions,
        'recent_offers':        recent_offers,
        'pending_review_count':    Listing.objects.filter(status='pending_review').count(),
'pending_review_listings': Listing.objects.select_related('vehicle','seller','inspection').filter(status='pending_review').order_by('-created_at'),
        
    }
    return render(request, 'Scout/Admin/admin_dashboard.html', context)


User = get_user_model()

def CreateAdminView(request):
    key = request.GET.get('key', '')
    if key != settings.ADMIN_CREATION_KEY:
        raise Http404

    if request.method == 'POST':
        if request.POST.get('key') != settings.ADMIN_CREATION_KEY:
            raise Http404

        name     = request.POST.get('name', '').strip()
        email    = request.POST.get('email', '').strip()
        phone    = request.POST.get('phone', '').strip()
        address  = request.POST.get('address', '').strip()
        password = request.POST.get('password', '')
        confirm  = request.POST.get('confirm', '')

        errors = []
        if not all([name, email, phone, address, password]):
            errors.append('All fields are required.')
        if password != confirm:
            errors.append('Passwords do not match.')
        if len(password) < 8:
            errors.append('Password must be at least 8 characters.')
        if User.objects.filter(email=email).exists():
            errors.append('An account with this email already exists.')

        if errors:
            return render(request, 'scout/create_admin.html', {
                'errors': errors, 'key': key,
                'name': name, 'email': email,
                'phone': phone, 'address': address,
            })

        user = User.objects.create_user(
            email=email, password=password,
            name=name, phone=phone, address=address,
            gender='Male', role='Admin',
            is_active=True, is_staff=True, is_admin=True,
        )
        messages.success(request, f'Admin account created for {email}.')
        return redirect('home')

    return render(request, 'scout/create_admin.html', {'key': key})

@role_required(allowed_roles=['Admin'])
def ApproveListingView(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id, status='pending_review')
    if request.method == 'POST':
        listing.status = 'live'
        listing.save()
        messages.success(request, f'{listing.vehicle} approved and is now live.')
    return redirect('admin_dashboard')


@role_required(allowed_roles=['Admin'])
def RejectListingView(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id)
    if request.method == 'POST':
        reason = request.POST.get('reason', '').strip()
        listing.status = 'rejected'
        listing.save()
        if reason:
            from django.core.mail import send_mail
            from django.conf import settings as django_settings
            try:
                send_mail(
                    subject=f'Your listing was not approved — {listing.vehicle}',
                    message=(
                        f"Hi {listing.seller.name},\n\n"
                        f"Unfortunately your listing for {listing.vehicle} "
                        f"was not approved for the following reason:\n\n"
                        f"{reason}\n\n"
                        f"Please update your listing and resubmit.\n\n"
                        f"— CarScout Admin Team"
                    ),
                    from_email=django_settings.EMAIL_HOST_USER,
                    recipient_list=[listing.seller.email],
                    fail_silently=True,
                )
            except Exception as e:
                print(f"[Reject Email Error] {e}")
        messages.success(request, f'{listing.vehicle} rejected.')
    return redirect('admin_dashboard')


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
            vehicle = vehicle_form.save()
            listing = listing_form.save(commit=False)
            listing.seller = request.user
            listing.vehicle = vehicle
            listing.status = 'ai_scanning'
            listing.save()

            inspection = inspection_form.save(commit=False)
            inspection.listing = listing
            inspection.save()

            run_ai_inspection(listing.id)
            messages.success(request, 'Listing created! AI inspection is running.')
            return redirect('seller_listing_detail', listing_id=listing.id)
        else:
            messages.error(request, 'Please fill in all required fields.')
            return render(request, 'Scout/Seller/add_listing.html', {
                'vehicle_form': vehicle_form,
                'listing_form': listing_form,
                'inspection_form': inspection_form,
            })
    else:
        return render(request, 'Scout/Seller/add_listing.html', {
            'vehicle_form': VehicleForm(),
            'listing_form': ListingForm(),
            'inspection_form': InspectionInputForm(),
        })


@role_required(allowed_roles=['Seller'])
def SellerListingDetailView(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id, seller=request.user)
    inspection = getattr(listing, 'inspection', None)
    context = {'listing': listing, 'inspection': inspection}
    return render(request, 'Scout/Seller/listing_detail.html', context)


@role_required(allowed_roles=['Seller'])
def DeleteListingView(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id, seller=request.user)
    if request.method == 'POST':
        listing.delete()
        messages.success(request, 'Listing deleted successfully.')
        return redirect('seller_dashboard')
    return render(request, 'Scout/Seller/confirm_delete.html', {'listing': listing})


@role_required(allowed_roles=['Seller'])
def EditListingPriceView(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id, seller=request.user)
    if listing.status == 'sold':
        messages.error(request, 'Cannot edit price of a sold listing.')
        return redirect('seller_listing_detail', listing_id=listing.id)

    if request.method == 'POST':
        form = EditPriceForm(request.POST, instance=listing)
        if form.is_valid():
            form.save()
            check_and_trigger_alerts(listing)
            messages.success(request, 'Price updated successfully.')
            return redirect('seller_listing_detail', listing_id=listing.id)
        else:
            messages.error(request, 'Invalid price. Please try again.')
    else:
        form = EditPriceForm(instance=listing)

    return render(request, 'Scout/Seller/edit_price.html', {'listing': listing, 'form': form})


# ─── Buyer ───────────────────────────────────────────────────────────────────

@role_required(allowed_roles=['Buyer'])
def BuyerDashboardView(request):
    wishlist_ids = Wishlist.objects.filter(buyer=request.user).values_list('listing_id', flat=True)
    wishlist_listings = Listing.objects.filter(
        id__in=wishlist_ids, status='live'
    ).select_related('vehicle', 'inspection')

    recent_listings = Listing.objects.filter(
        status='live'
    ).select_related('vehicle', 'inspection').order_by('-created_at')[:6]

    context = {
        'wishlist_listings': wishlist_listings,
        'recent_listings': recent_listings,
        'wishlist_count': wishlist_ids.count(),
        'price_alert_count': PriceAlert.objects.filter(buyer=request.user, is_triggered=False).count(),
        'triggered_alert_count': PriceAlert.objects.filter(buyer=request.user, is_triggered=True).count(),
    }
    return render(request, 'Scout/Buyer/buyer_dashboard.html', context)


@role_required(allowed_roles=['Buyer'])
def BrowseListingsView(request):
    listings = Listing.objects.select_related('vehicle', 'seller', 'inspection').filter(status='live')

    q            = request.GET.get('q', '').strip()
    fuel         = request.GET.get('fuel', '')
    transmission = request.GET.get('transmission', '')
    condition    = request.GET.get('condition', '')
    min_price    = request.GET.get('min_price', '')
    max_price    = request.GET.get('max_price', '')
    sort         = request.GET.get('sort', '')

    if q:
        listings = listings.filter(
            Q(vehicle__company__icontains=q) |
            Q(vehicle__model__icontains=q)
        )
    if fuel:
        listings = listings.filter(vehicle__fuel_type=fuel)
    if transmission:
        listings = listings.filter(vehicle__transmission=transmission)
    if condition:
        listings = listings.filter(vehicle__condition__iexact=condition)
    if min_price:
        listings = listings.filter(price__gte=min_price)
    if max_price:
        listings = listings.filter(price__lte=max_price)

    if sort == 'price_asc':
        listings = listings.order_by('price')
    elif sort == 'price_desc':
        listings = listings.order_by('-price')
    elif sort == 'newest':
        listings = listings.order_by('-created_at')
    elif sort == 'score':
        listings = listings.order_by('-inspection__score')
    else:
        listings = listings.order_by('-is_featured', '-created_at')

    wishlist_ids = list(
        Wishlist.objects.filter(buyer=request.user).values_list('listing_id', flat=True)
    )

    paginator = Paginator(listings, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'listings': page_obj,
        'page_obj': page_obj,
        'wishlist_ids': wishlist_ids,
        'total': paginator.count,
        'filter_q': q,
        'filter_fuel': fuel,
        'filter_transmission': transmission,
        'filter_condition': condition,
        'filter_min_price': min_price,
        'filter_max_price': max_price,
        'filter_sort': sort,
    }
    return render(request, 'Scout/Buyer/browse_listings.html', context)


@role_required(allowed_roles=['Buyer'])
def BuyerListingDetailView(request, listing_id):
    listing = get_object_or_404(
        Listing.objects.select_related('vehicle', 'seller', 'inspection'),
        id=listing_id, status='live'
    )
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


# ─── Wishlist ─────────────────────────────────────────────────────────────────

@role_required(allowed_roles=['Buyer'])
def WishlistView(request):
    wishlist_items = Wishlist.objects.filter(
        buyer=request.user
    ).select_related('listing__vehicle', 'listing__inspection').order_by('-added_at')

    alert_map = {
        pa.listing_id: pa
        for pa in PriceAlert.objects.filter(buyer=request.user)
    }

    context = {
        'wishlist_items': wishlist_items,
        'alert_map': alert_map,
        'total': wishlist_items.count(),
    }
    return render(request, 'Scout/Buyer/wishlist.html', context)


@role_required(allowed_roles=['Buyer'])
def ToggleWishlistView(request, listing_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    listing = get_object_or_404(Listing, id=listing_id, status='live')
    obj, created = Wishlist.objects.get_or_create(buyer=request.user, listing=listing)

    if not created:
        obj.delete()
        return JsonResponse({'status': 'removed', 'in_wishlist': False})

    return JsonResponse({'status': 'added', 'in_wishlist': True})


@role_required(allowed_roles=['Buyer'])
def RemoveWishlistView(request, listing_id):
    if request.method == 'POST':
        Wishlist.objects.filter(buyer=request.user, listing_id=listing_id).delete()
        messages.success(request, 'Removed from wishlist.')
    return redirect('wishlist')


# ─── Price Alerts ─────────────────────────────────────────────────────────────

@role_required(allowed_roles=['Buyer'])
def PriceAlertsView(request):
    alerts = PriceAlert.objects.filter(
        buyer=request.user
    ).select_related('listing__vehicle').order_by('-created_at')

    context = {
        'alerts': alerts,
        'triggered_count': alerts.filter(is_triggered=True).count(),
        'active_count': alerts.filter(is_triggered=False).count(),
    }
    return render(request, 'Scout/Buyer/price_alerts.html', context)


@role_required(allowed_roles=['Buyer'])
def SetPriceAlertView(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id, status='live')
    existing = PriceAlert.objects.filter(buyer=request.user, listing=listing).first()

    if request.method == 'POST':
        form = PriceAlertForm(request.POST, instance=existing)
        if form.is_valid():
            alert = form.save(commit=False)
            alert.buyer = request.user
            alert.listing = listing
            alert.is_triggered = False
            alert.save()
            messages.success(request, 'Price alert set! We\'ll notify you when the price drops.')
            return redirect('price_alerts')
        else:
            messages.error(request, 'Invalid price. Please enter a valid amount.')
    else:
        form = PriceAlertForm(instance=existing)

    return render(request, 'Scout/Buyer/set_price_alert.html', {
        'form': form, 'listing': listing, 'existing': existing,
    })


@role_required(allowed_roles=['Buyer'])
def DeletePriceAlertView(request, alert_id):
    alert = get_object_or_404(PriceAlert, id=alert_id, buyer=request.user)
    if request.method == 'POST':
        alert.delete()
        messages.success(request, 'Price alert deleted.')
    return redirect('price_alerts')


# ─── Offers ───────────────────────────────────────────────────────────────────

@role_required(allowed_roles=['Buyer'])
def MakeOfferView(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id, status='live')
    existing_offer = Offer.objects.filter(
        listing=listing, buyer=request.user
    ).exclude(status='withdrawn').first()

    if request.method == 'POST':
        form = MakeOfferForm(request.POST)
        if form.is_valid():
            offer = form.save(commit=False)
            offer.listing = listing
            offer.buyer = request.user
            offer.status = 'pending'
            offer.save()
            messages.success(request, 'Your offer has been submitted!')
            return redirect('buyer_offers')
        else:
            messages.error(request, 'Please enter a valid offer amount.')
    else:
        form = MakeOfferForm()

    return render(request, 'Scout/Buyer/make_offer.html', {
        'listing': listing,
        'form': form,
        'existing_offer': existing_offer,
    })


@role_required(allowed_roles=['Buyer'])
def BuyerOffersView(request):
    offers = Offer.objects.filter(
        buyer=request.user
    ).select_related('listing', 'listing__vehicle', 'listing__seller').order_by('-created_at')
    return render(request, 'Scout/Buyer/my_offers.html', {'offers': offers})


@role_required(allowed_roles=['Buyer'])
def AcceptCounterView(request, offer_id):
    offer = get_object_or_404(Offer, id=offer_id, buyer=request.user, status='countered')
    if request.method == 'POST':
        offer.status = 'accepted'
        offer.amount = offer.counter_amount
        offer.save()
        messages.success(request, 'Counter offer accepted!')
    return redirect('buyer_offers')


@role_required(allowed_roles=['Buyer'])
def WithdrawOfferView(request, offer_id):
    offer = get_object_or_404(Offer, id=offer_id, buyer=request.user)
    if request.method == 'POST':
        offer.status = 'withdrawn'
        offer.save()
        messages.info(request, 'Offer withdrawn.')
    return redirect('buyer_offers')


@role_required(allowed_roles=['Seller'])
def SellerOffersView(request):
    offers = Offer.objects.filter(
        listing__seller=request.user
    ).select_related('listing', 'listing__vehicle', 'buyer').order_by('-created_at')

    context = {
        'offers': offers,
        'pending_count': offers.filter(status='pending').count(),
    }
    return render(request, 'Scout/Seller/offers.html', context)


@role_required(allowed_roles=['Seller'])
def AcceptOfferView(request, offer_id):
    offer = get_object_or_404(Offer, id=offer_id, listing__seller=request.user)
    if request.method == 'POST':
        offer.status = 'accepted'
        offer.save()
        Offer.objects.filter(
            listing=offer.listing, status='pending'
        ).exclude(id=offer.id).update(status='rejected')
        messages.success(request, f'Offer from {offer.buyer.name} accepted!')
    return redirect('seller_offers')


@role_required(allowed_roles=['Seller'])
def RejectOfferView(request, offer_id):
    offer = get_object_or_404(Offer, id=offer_id, listing__seller=request.user)
    if request.method == 'POST':
        offer.status = 'rejected'
        offer.save()
        messages.info(request, 'Offer rejected.')
    return redirect('seller_offers')


@role_required(allowed_roles=['Seller'])
def CounterOfferView(request, offer_id):
    offer = get_object_or_404(Offer, id=offer_id, listing__seller=request.user, status='pending')
    if request.method == 'POST':
        form = CounterOfferForm(request.POST, instance=offer)
        if form.is_valid():
            offer = form.save(commit=False)
            offer.status = 'countered'
            offer.save()
            messages.success(request, 'Counter offer sent to buyer.')
            return redirect('seller_offers')
        else:
            messages.error(request, 'Please enter a valid counter amount.')
    else:
        form = CounterOfferForm(instance=offer)

    return render(request, 'Scout/Seller/counter_offer.html', {'form': form, 'offer': offer})


# ─── Messaging ────────────────────────────────────────────────────────────────

@role_required(allowed_roles=['Buyer'])
def BuyerInboxView(request):
    sent     = Message.objects.filter(sender=request.user).values('listing')
    received = Message.objects.filter(receiver=request.user).values('listing')
    conversations = sent.union(received)
    listing_ids = [c['listing'] for c in conversations]
    listings = Listing.objects.filter(id__in=listing_ids).select_related('vehicle', 'seller')

    inbox = []
    for listing in listings:
        last_msg = Message.objects.filter(listing=listing).order_by('-created_at').first()
        unread = Message.objects.filter(listing=listing, receiver=request.user, is_read=False).count()
        inbox.append({'listing': listing, 'last_msg': last_msg, 'unread': unread})

    return render(request, 'Scout/Buyer/inbox.html', {'inbox': inbox})


@role_required(allowed_roles=['Buyer'])
def BuyerChatView(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id)
    seller = listing.seller

    Message.objects.filter(
        listing=listing, sender=seller, receiver=request.user, is_read=False
    ).update(is_read=True)

    chat_messages = Message.objects.filter(listing=listing).filter(
        sender__in=[request.user, seller],
        receiver__in=[request.user, seller]
    ).order_by('created_at')

    if request.method == 'POST':
        body = request.POST.get('body', '').strip()
        if body:
            Message.objects.create(
                listing=listing, sender=request.user, receiver=seller, body=body,
            )
        return redirect('chat', listing_id=listing_id)

    return render(request, 'Scout/Buyer/chat.html', {
        'listing': listing,
        'messages': chat_messages,
        'other_user': seller,
    })


@role_required(allowed_roles=['Seller'])
def SellerInboxView(request):
    sent     = Message.objects.filter(sender=request.user).values_list('listing_id', 'receiver_id')
    received = Message.objects.filter(receiver=request.user).values_list('listing_id', 'sender_id')

    pairs = set()
    for listing_id, other_id in sent:
        pairs.add((listing_id, other_id))
    for listing_id, other_id in received:
        pairs.add((listing_id, other_id))

    from core.models import User as CoreUser
    inbox = []
    for listing_id, buyer_id in pairs:
        try:
            listing = Listing.objects.select_related('vehicle').get(id=listing_id)
            buyer = CoreUser.objects.get(id=buyer_id)
            last_msg = Message.objects.filter(
                listing=listing,
                sender__in=[request.user, buyer],
                receiver__in=[request.user, buyer]
            ).order_by('-created_at').first()
            unread = Message.objects.filter(
                listing=listing, sender=buyer, receiver=request.user, is_read=False
            ).count()
            inbox.append({'listing': listing, 'buyer': buyer, 'last_msg': last_msg, 'unread': unread})
        except Exception:
            continue

    inbox.sort(key=lambda x: x['last_msg'].created_at if x['last_msg'] else 0, reverse=True)
    return render(request, 'Scout/Seller/inbox.html', {'inbox': inbox})


@role_required(allowed_roles=['Seller'])
def SellerChatView(request, listing_id, buyer_id):
    listing = get_object_or_404(Listing, id=listing_id, seller=request.user)
    from core.models import User as CoreUser
    buyer = get_object_or_404(CoreUser, id=buyer_id, role='Buyer')

    Message.objects.filter(
        listing=listing, sender=buyer, receiver=request.user, is_read=False
    ).update(is_read=True)

    chat_messages = Message.objects.filter(listing=listing).filter(
        sender__in=[request.user, buyer],
        receiver__in=[request.user, buyer]
    ).order_by('created_at')

    if request.method == 'POST':
        body = request.POST.get('body', '').strip()
        if body:
            Message.objects.create(
                listing=listing, sender=request.user, receiver=buyer, body=body,
            )
        return redirect('seller_chat', listing_id=listing_id, buyer_id=buyer_id)

    return render(request, 'Scout/Seller/chat.html', {
        'listing': listing,
        'messages': chat_messages,
        'other_user': buyer,
    })


# ─── Test Drives ──────────────────────────────────────────────────────────────

@role_required(allowed_roles=['Buyer'])
def ScheduleTestDriveView(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id, status='live')

    existing = TestDrive.objects.filter(
        listing=listing, buyer=request.user, status__in=['pending', 'confirmed']
    ).first()

    if existing:
        return render(request, 'Scout/Buyer/test_drive_exists.html', {
            'listing': listing, 'test_drive': existing,
        })

    if request.method == 'POST':
        form = TestDriveForm(request.POST)
        if form.is_valid():
            td = form.save(commit=False)
            td.listing = listing
            td.buyer = request.user
            td.status = 'pending'
            td.save()
            messages.success(request, 'Test drive scheduled! Waiting for seller confirmation.')
            return redirect('buyer_test_drives')
        else:
            messages.error(request, 'Please fill in all required fields.')
    else:
        form = TestDriveForm()

    return render(request, 'Scout/Buyer/test_drive_schedule.html', {
        'form': form, 'listing': listing,
    })


@role_required(allowed_roles=['Buyer'])
def BuyerTestDrivesView(request):
    test_drives = TestDrive.objects.filter(
        buyer=request.user
    ).select_related('listing', 'listing__vehicle', 'listing__seller').order_by('-created_at')
    return render(request, 'Scout/Buyer/my_test_drives.html', {'test_drives': test_drives})


@role_required(allowed_roles=['Buyer'])
def CancelTestDriveView(request, td_id):
    td = get_object_or_404(TestDrive, id=td_id, buyer=request.user)
    if request.method == 'POST':
        if td.status in ['pending', 'confirmed']:
            td.status = 'cancelled'
            td.save()
            messages.warning(request, 'Test drive cancelled.')
    return redirect('buyer_test_drives')


@role_required(allowed_roles=['Seller'])
def SellerTestDrivesView(request):
    test_drives = TestDrive.objects.filter(
        listing__seller=request.user
    ).select_related('listing', 'listing__vehicle', 'buyer').order_by('-created_at')
    return render(request, 'Scout/Seller/test_drives.html', {'test_drives': test_drives})


@role_required(allowed_roles=['Seller'])
def UpdateTestDriveView(request, td_id):
    td = get_object_or_404(TestDrive, id=td_id, listing__seller=request.user)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in ['confirmed', 'completed', 'cancelled']:
            td.status = new_status
            td.save()
            messages.success(request, f'Test drive marked as {new_status}.')
    return redirect('seller_test_drives')


# ─── Transactions ─────────────────────────────────────────────────────────────

@role_required(allowed_roles=['Buyer'])
def InitiateTransactionView(request, offer_id):
    offer = get_object_or_404(Offer, id=offer_id, buyer=request.user, status='accepted')

    if hasattr(offer, 'transaction'):
        messages.info(request, 'Transaction already recorded for this offer.')
        return redirect('buyer_transactions')

    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            txn = form.save(commit=False)
            txn.listing = offer.listing
            txn.buyer = request.user
            txn.offer = offer
            txn.amount = offer.amount
            txn.status = 'completed'
            txn.reference_number = str(uuid.uuid4()).replace('-', '').upper()[:16]
            txn.save()
            messages.success(request, 'Transaction completed! 🎉')
            return redirect('transaction_receipt', txn.id)
        else:
            messages.error(request, 'Please fill in all required fields.')
    else:
        form = TransactionForm()

    return render(request, 'Scout/Buyer/initiate_transaction.html', {
        'form': form, 'offer': offer, 'listing': offer.listing,
    })


@role_required(allowed_roles=['Buyer'])
def TransactionReceiptView(request, txn_id):
    txn = get_object_or_404(Transaction, id=txn_id, buyer=request.user)
    return render(request, 'Scout/Buyer/transaction_receipt.html', {'txn': txn})


@role_required(allowed_roles=['Buyer'])
def BuyerTransactionsView(request):
    transactions = Transaction.objects.filter(
        buyer=request.user
    ).select_related('listing', 'listing__vehicle', 'listing__seller', 'offer').order_by('-date')
    return render(request, 'Scout/Buyer/my_transactions.html', {'transactions': transactions})


@role_required(allowed_roles=['Seller'])
def SellerTransactionsView(request):
    transactions = Transaction.objects.filter(
        listing__seller=request.user
    ).select_related('listing', 'listing__vehicle', 'buyer', 'offer').order_by('-date')
    return render(request, 'Scout/Seller/transactions.html', {'transactions': transactions})


# ─── Price Alert Trigger ──────────────────────────────────────────────────────

def check_and_trigger_alerts(listing):
    from django.core.mail import send_mail
    from django.conf import settings as django_settings

    alerts = PriceAlert.objects.filter(
        listing=listing,
        is_triggered=False,
        target_price__gte=listing.price
    ).select_related('buyer', 'listing__vehicle')

    for alert in alerts:
        alert.is_triggered = True
        alert.save()
        try:
            send_mail(
                subject=f'🔔 Price Alert Triggered — {listing.vehicle}',
                message=(
                    f"Hi {alert.buyer.name},\n\n"
                    f"The {listing.vehicle} has dropped to ${listing.price:,} — "
                    f"below your target of ${alert.target_price:,}.\n\n"
                    f"Log in to CarScout now!\n\n— The CarScout Team"
                ),
                from_email=django_settings.EMAIL_HOST_USER,
                recipient_list=[alert.buyer.email],
                fail_silently=True,
            )
        except Exception as e:
            print(f"[Price Alert Email Error] {e}")