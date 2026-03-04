from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from scout.decorators import role_required
from .form import listingForm,VehicleForm,InspectionReportForm,TestDriveForm,OfferForm,TransactionForm
from django.shortcuts import get_object_or_404
from .models import Listing, Vehicle
# Create your views here.
@role_required(allowed_roles=['Admin'])
def AdminDashboardView(request):
    return render(request,'Scout/Admin/admin_dashboard.html')

@role_required(allowed_roles=['Seller'])
def SellerDashboardView(request):
    listings = Listing.objects.filter(seller=request.user).select_related('vehicle').order_by('-id')
    return render(request,'Scout/Seller/seller_dashboard.html', {'listings': listings})

@role_required(allowed_roles=['Buyer'])
def BuyerDashboardView(request):
    return render(request,'Scout/Buyer/buyer_dashboard.html')

@role_required(allowed_roles=['Seller'])
def select_vehicle(request):
    vehicles = Vehicle.objects.filter(listing__isnull=True)
    return render(request, 'Scout/Seller/select_vehicle.html', {'vehicles': vehicles})
@role_required(allowed_roles=['Seller'])
def listing(request, vehicle_id):
    vehicle_obj = get_object_or_404(Vehicle, id=vehicle_id)  # ← already there, good
    if request.method == 'POST':
        form = listingForm(request.POST, request.FILES)
        if form.is_valid():
            listing_obj = form.save(commit=False)
            listing_obj.seller = request.user
            listing_obj.vehicle = vehicle_obj
            listing_obj.save()
            return redirect('seller_dashboard')
        else:
            print(form.errors)
            return render(request, 'Scout/Seller/listing.html', {'form': form, 'vehicle': vehicle_obj})
    else:
        form = listingForm()
    return render(request, 'Scout/Seller/listing.html', {'form': form, 'vehicle': vehicle_obj})

@role_required(allowed_roles=['Seller'])
def add_vehicle(request):
    if request.method=='POST':
        form=VehicleForm(request.POST or None)
        if form.is_valid():
            vehicle = form.save()
            return redirect('listing', vehicle_id=vehicle.id)
        else:
            print(form.errors)
            return render(request,'Scout/Seller/add_vehicle.html',{'form':form})
    else:
        form=VehicleForm()
    return render(request,'Scout/Seller/add_vehicle.html',{'form':form})

@role_required(allowed_roles=['Admin'])
def inspection_report(request):
    if request.method=='POST':
        form=InspectionReportForm(request.POST or None)
        if form.is_valid():
            form.save()
            return redirect('seller_dashboard')
        else:
            print(form.errors)
            return render(request,'Scout/Admin/inspection_report.html',{'form':form})
    else:
        form=InspectionReportForm()
    return render(request,'Scout/Admin/inspection_report.html',{'form':form})

@role_required(allowed_roles=['Buyer','Seller','Admin'])
def listing_detail(request, listing_id):
    listing_obj = get_object_or_404(
        Listing.objects.select_related('seller', 'vehicle'),  # ← fetch related objects
        id=listing_id
    )
    
    # Get inspection report safely
    try:
        inspection = listing_obj.inspectionreport_set.latest('generated_at')
    except:
        inspection = None

    return render(request, 'Scout/Buyer/listing_detail.html', {
        'listing': listing_obj,
        'inspection': inspection
    })

@role_required(allowed_roles=['Buyer'])
def test_drive(request, listing_id):
    listing_obj = get_object_or_404(Listing, id=listing_id)
    if request.method=='POST':
        form=TestDriveForm(request.POST or None)
        if form.is_valid():
            td = form.save(commit=False)
            td.buyer = request.user
            td.listing = listing_obj
            td.save()
            return redirect('buyer_dashboard')
        else:
            print(form.errors)
            return render(request,'Scout/Buyer/test_drive.html',{'form':form, 'listing': listing_obj})
    else:
        form=TestDriveForm()
    return render(request,'Scout/Buyer/test_drive.html',{'form':form, 'listing': listing_obj})

@role_required(allowed_roles=['Buyer'])
def offer(request, listing_id):
    listing_obj = get_object_or_404(Listing, id=listing_id)
    if request.method=='POST':
        form=OfferForm(request.POST or None)
        if form.is_valid():
            offer_obj = form.save(commit=False)
            offer_obj.buyer = request.user
            offer_obj.listing = listing_obj
            offer_obj.save()
            return redirect('buyer_dashboard')
        else:
            print(form.errors)
            return render(request,'Scout/Buyer/offer.html',{'form':form, 'listing': listing_obj})
    else:
        form=OfferForm()
    return render(request,'Scout/Buyer/offer.html',{'form':form, 'listing': listing_obj})

@role_required(allowed_roles=['Admin'])
def transaction(request):
    if request.method=='POST':
        form=TransactionForm(request.POST or None)
        if form.is_valid():
            form.save()
            return redirect('seller_dashboard')
        else:
            print(form.errors)
            return render(request,'Scout/Admin/transaction.html',{'form':form})
    else:
        form=TransactionForm()
    return render(request,'Scout/Admin/transaction.html',{'form':form})