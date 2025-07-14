from django.urls import path
from .views import (
    RegisterView, LoginView, ForgotPasswordView, ProfileView, PhotoUploadView,
    PhotoDeleteView, wallet_amount, get_live_prices, purchase_tokens, sell_tokens, user_transactions,
    purchased_token_summary, token_balances, user_sell_transactions, profit_loss_summary
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('reset-password/', ForgotPasswordView.as_view(), name='reset_password'),
    path('profile/<str:email>/', ProfileView.as_view(), name='profile'),
    path('photo-upload/<str:email>/', PhotoUploadView.as_view(), name='photo_upload'),
    path('photo-delete/<str:email>/', PhotoDeleteView.as_view(), name='photo_delete'),
    path('wallet-amount/<str:email>/', wallet_amount, name='wallet_amount'),
    path('live-prices/', get_live_prices, name='get_live_prices'),
    path('purchase-tokens/', purchase_tokens, name='purchase_tokens'),
    path('sell-tokens/', sell_tokens, name='sell_tokens'),
    path('transactions/<str:email>/', user_transactions, name='user_transactions'),
    path('purchased-token-summary/<str:email>/', purchased_token_summary, name='purchased_token_summary'),
    path('token-balances/<str:email>/', token_balances, name='token_balances'),
    path('sell-transactions/<str:email>/', user_sell_transactions, name='sell_transactions'),
    path('profit-loss-summary/<str:email>/', profit_loss_summary, name='profit_loss_summary'),
    path('profile-full/<str:email>/', ProfileView.as_view(), name='full_profile_view'),
]