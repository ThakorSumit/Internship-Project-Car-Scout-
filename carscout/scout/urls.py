from django.urls import path
from . import views
from django.views.generic import TemplateView
urlpatterns = [
    # Admin
    path('admin/', views.AdminDashboardView, name='admin_dashboard'),
    path('admin/listing/<int:listing_id>/approve/', views.ApproveListingView, name='approve_listing'),
    path('admin/listing/<int:listing_id>/reject/',  views.RejectListingView,  name='reject_listing'),
    path('admin/listing/<int:listing_id>/inspection/', views.AdminInspectionReportView.as_view(), name='admin_inspection_report'),
    #http://localhost:8000/createadmin/?key=carscout
    
    # Seller
    path('seller/', views.SellerDashboardView, name='seller_dashboard'),
    path('seller/add-listing/', views.AddListingView, name='add_listing'),
    path('seller/listing/<int:listing_id>/', views.SellerListingDetailView, name='seller_listing_detail'),
    path('seller/listing/<int:listing_id>/delete/', views.DeleteListingView, name='delete_listing'),
    path('seller/listing/<int:listing_id>/edit-price/', views.EditListingPriceView, name='edit_listing_price'),
    path('seller/offers/', views.SellerOffersView, name='seller_offers'),
    path('seller/offer/<int:offer_id>/accept/', views.AcceptOfferView, name='accept_offer'),
    path('seller/offer/<int:offer_id>/reject/', views.RejectOfferView, name='reject_offer'),
    path('seller/offer/<int:offer_id>/counter/', views.CounterOfferView, name='counter_offer'),
    path('seller/inbox/', views.SellerInboxView, name='seller_inbox'),
    path('seller/chat/<int:listing_id>/<int:buyer_id>/', views.SellerChatView, name='seller_chat'),
    path('seller/test-drives/', views.SellerTestDrivesView, name='seller_test_drives'),
    path('seller/test-drives/<int:td_id>/update/', views.UpdateTestDriveView, name='update_test_drive'),
    path('seller/transactions/', views.SellerTransactionsView, name='seller_transactions'),

    # Buyer
    path('buyer/', views.BuyerDashboardView, name='buyer_dashboard'),
    path('buyer/browse/', views.BrowseListingsView, name='browse_listings'),
    path('buyer/listing/<int:listing_id>/', views.BuyerListingDetailView, name='buyer_listing_detail'),
    path('buyer/offer/<int:listing_id>/', views.MakeOfferView, name='offer'),
    path('buyer/offers/', views.BuyerOffersView, name='buyer_offers'),
    path('buyer/offer/<int:offer_id>/accept-counter/', views.AcceptCounterView, name='accept_counter'),
    path('buyer/offer/<int:offer_id>/withdraw/', views.WithdrawOfferView, name='withdraw_offer'),
    path('buyer/inbox/', views.BuyerInboxView, name='buyer_inbox'),
    path('buyer/chat/<int:listing_id>/', views.BuyerChatView, name='chat'),
    path('buyer/test-drives/', views.BuyerTestDrivesView, name='buyer_test_drives'),
    path('buyer/test-drives/<int:listing_id>/schedule/', views.ScheduleTestDriveView, name='test_drive'),
    path('buyer/test-drives/<int:td_id>/cancel/', views.CancelTestDriveView, name='cancel_test_drive'),
    path('buyer/transactions/', views.BuyerTransactionsView, name='buyer_transactions'),
    path('buyer/compare/', views.CompareView.as_view(), name='compare'),

    #payment
    path('payment/<int:offer_id>/select/',          views.PaymentSelectView,       name='payment_select'),
    path('payment/<int:offer_id>/cash/',            views.CashPaymentView,         name='cash_payment'),
    path('payment/<int:offer_id>/razorpay/create/', views.RazorpayCreateOrderView, name='razorpay_create_order'),
    path('payment/<int:offer_id>/razorpay/verify/', views.RazorpayVerifyView,      name='razorpay_verify'),
    path('transaction/<int:txn_id>/receipt/',       views.TransactionReceiptView,  name='transaction_receipt'),
    
    # Wishlist
    path('buyer/wishlist/', views.WishlistView, name='wishlist'),
    path('buyer/wishlist/toggle/<int:listing_id>/', views.ToggleWishlistView, name='toggle_wishlist'),
    path('buyer/wishlist/remove/<int:listing_id>/', views.RemoveWishlistView, name='remove_wishlist'),

    # Price Alerts
    path('buyer/price-alerts/', views.PriceAlertsView, name='price_alerts'),
    path('buyer/price-alerts/set/<int:listing_id>/', views.SetPriceAlertView, name='set_price_alert'),
    path('buyer/price-alerts/delete/<int:alert_id>/', views.DeletePriceAlertView, name='delete_price_alert'),


    #T&C and Privacy Policy
    path('terms-and-conditions/', TemplateView.as_view(template_name='Scout/terms_and_conditions.html'), name='terms_and_conditions'),
    path('privacy-policy/', TemplateView.as_view(template_name='Scout/privacy_policy.html'), name='privacy_policy'),
]