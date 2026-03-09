from django.urls import path
from . import views

urlpatterns = [
    # Admin
    path('admin/', views.AdminDashboardView, name='admin_dashboard'),

    # Seller
    path('seller/', views.SellerDashboardView, name='seller_dashboard'),
    path('seller/add-listing/', views.AddListingView, name='add_listing'),
    path('seller/listing/<int:listing_id>/', views.SellerListingDetailView, name='seller_listing_detail'),
    path('seller/listing/<int:listing_id>/delete/', views.DeleteListingView, name='delete_listing'),
    path('seller/test-drives/', views.SellerTestDrivesView, name='seller_test_drives'),
    path('seller/test-drives/<int:td_id>/update/', views.UpdateTestDriveView, name='update_test_drive'),
    path('seller/transactions/', views.SellerTransactionsView, name='seller_transactions'),

    # Buyer
    path('buyer/', views.BuyerDashboardView, name='buyer_dashboard'),
    path('buyer/browse/', views.BrowseListingsView, name='browse_listings'),
    path('buyer/listing/<int:listing_id>/', views.BuyerListingDetailView, name='buyer_listing_detail'),
    path('buyer/listing/<int:listing_id>/toggle-wishlist/', views.ToggleWishlistView, name='toggle_wishlist'),
    path('buyer/test-drives/', views.BuyerTestDrivesView, name='buyer_test_drives'),
    path('buyer/test-drives/<int:td_id>/cancel/', views.CancelTestDriveView, name='cancel_test_drive'),
    path('buyer/listing/<int:listing_id>/test-drive/', views.ScheduleTestDriveView, name='test_drive'),
    path('buyer/offers/', views.BuyerOffersView, name='buyer_offers'),
    path('buyer/offers/<int:offer_id>/pay/', views.InitiateTransactionView, name='initiate_transaction'),
    path('buyer/transactions/', views.BuyerTransactionsView, name='buyer_transactions'),
    path('buyer/transactions/<int:txn_id>/receipt/', views.TransactionReceiptView, name='transaction_receipt'),

    # Offer URLs
    path('buyer/offer/<int:listing_id>/', views.MakeOfferView, name='make_offer'),
    path('buyer/offers/', views.BuyerOffersView, name='buyer_offers'),
    path('buyer/offer/<int:offer_id>/accept/', views.AcceptCounterView, name='accept_counter'),
    path('buyer/offer/<int:offer_id>/withdraw/', views.WithdrawOfferView, name='withdraw_offer'),

    path('seller/offers/', views.SellerOffersView, name='seller_offers'),
    path('seller/offer/<int:offer_id>/accept/', views.AcceptOfferView, name='accept_offer'),
    path('seller/offer/<int:offer_id>/reject/', views.RejectOfferView, name='reject_offer'),
    path('seller/offer/<int:offer_id>/counter/', views.CounterOfferView, name='counter_offer'),

    # Messaging URLs
    path('buyer/inbox/', views.BuyerInboxView, name='buyer_inbox'),
    path('buyer/chat/<int:listing_id>/', views.BuyerChatView, name='buyer_chat'),
    path('seller/inbox/', views.SellerInboxView, name='seller_inbox'),
    path('seller/chat/<int:listing_id>/<int:buyer_id>/', views.SellerChatView, name='seller_chat'),


]