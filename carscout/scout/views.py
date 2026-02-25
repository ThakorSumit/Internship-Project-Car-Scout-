from django.shortcuts import render
from django.contrib.auth.decorators import login_required
# Create your views here.
@login_required(login_url={('login')})
def AdminDashboardView(request):
    return render(request,'scout/admin_dashboard.html')

@login_required(login_url={('login')})
def SellerDashboardView(request):
    return render(request,'scout/seller_dashboard.html')

@login_required(login_url={('login')})
def BuyerDashboardView(request):
    return render(request,'scout/buyer_dashboard.html')