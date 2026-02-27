from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from scout.decorators import role_required
# Create your views here.
@role_required(allowed_roles=['Admin'])
def AdminDashboardView(request):
    return render(request,'Scout/Admin/admin_dashboard.html')

@role_required(allowed_roles=['Seller'])
def SellerDashboardView(request):
    return render(request,'Scout/Seller/seller_dashboard.html')

@role_required(allowed_roles=['Buyer'])
def BuyerDashboardView(request):
    return render(request,'Scout/Buyer/buyer_dashboard.html')


    