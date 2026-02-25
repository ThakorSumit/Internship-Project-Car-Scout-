from django.urls import path
from . import views

urlpatterns = [
   path('admin/',views.AdminDashboardView,name='admin_dashboard'),
   path('seller/',views.SellerDashboardView,name='seller_dashboard'),
   path('buyer/',views.BuyerDashboardView,name='buyer_dashboard'),
]