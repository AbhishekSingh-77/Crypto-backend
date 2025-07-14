from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.cache import cache
from django.db.models import Sum
from django.conf import settings
from decimal import Decimal
from .models import Register, Profile, Transaction, TokenBalance, ProfitLossSummary
from .serializers import RegisterSerializer, LoginSerializer, TransactionSerializer
import requests
import re

# Utility function for fetching live prices
def fetch_live_prices(ids, vs_currencies='usd'):
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {'ids': ids, 'vs_currencies': vs_currencies}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        return {}

# Register View
class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        self.perform_create(serializer)
        return Response({"message": "Registered successfully."}, status=status.HTTP_201_CREATED)

# Login View
class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['user']
            register_serializer = RegisterSerializer(email)
            return Response({
                'message': 'Login successful.',
                'register_details': register_serializer.data
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Forgot Password View
class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        question = request.data.get('question')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')

        if not all([email, question, new_password, confirm_password]):
            return Response({'message': 'All fields are required.'}, status=400)

        try:
            user = Register.objects.get(email=email)
        except Register.DoesNotExist:
            return Response({'message': 'Email not registered.'}, status=404)

        if user.security_question.lower() != question.lower():
            return Response({'message': 'Security question answer is incorrect.'}, status=400)

        if new_password != confirm_password:
            return Response({'message': 'Passwords do not match.'}, status=400)

        if len(new_password) < 7 or not re.match(r'^(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])', new_password):
            return Response({'message': 'Password must have 1 uppercase, 1 number, and 1 special character.'}, status=400)

        user.password = new_password
        user.save()

        return Response({'message': 'Password reset successful.'}, status=200)

# Profile View
class ProfileView(APIView):
    def get(self, request, email):
        try:
            user = Register.objects.get(email=email)
            profile = user.profile
        except Register.DoesNotExist:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        data = {
            'username': user.username,
            'email': user.email,
            'dob': user.dob,
            'photo_url': request.build_absolute_uri(profile.photo_url.url) if profile.photo_url else '',
            'created_at': user.created_at
        }

        return Response(data, status=status.HTTP_200_OK)
    
    def delete(self, request, email):
        try:
            user = Register.objects.get(email=email)
            user.delete()
            return Response({'message': 'Account deleted successfully.'}, status=status.HTTP_200_OK)
        except Register.DoesNotExist:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        
    def put(self, request, email):
        try:
            user = Register.objects.get(email=email)
        except Register.DoesNotExist:
            return Response({'error': 'User not found.'}, status=404)

        current_answer = request.data.get('current_security_answer')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')

        if not all([current_answer, new_password, confirm_password]):
            return Response({'error': 'All fields are required.'}, status=400)

        if user.security_question.lower() != current_answer.lower():
            return Response({'error': 'Incorrect security answer.'}, status=400)

        if new_password != confirm_password:
            return Response({'error': 'Passwords do not match.'}, status=400)

        if len(new_password) < 7 or not re.match(r'^(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])', new_password):
            return Response({'error': 'Password must have 1 uppercase, 1 number, and 1 special character.'}, status=400)

        user.password = new_password
        user.save()

        return Response({'message': 'Password updated successfully.'}, status=200)

# User Profile Image Upload View
class PhotoUploadView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, email):
        try:
            user = Register.objects.get(email=email)
        except Register.DoesNotExist:
            return Response({'error': 'User not found.'}, status=404)

        photo = request.FILES.get('photo')
        if not photo:
            return Response({'error': 'No photo uploaded.'}, status=400)

        user.profile.photo_url = photo
        user.profile.save()
        
        photo_url = request.build_absolute_uri(user.profile.photo_url.url)
        return Response({'message': 'Photo uploaded successfully.', 'photo_url': photo_url}, status=200)

# User Profile Image Delete View
class PhotoDeleteView(APIView):
    def delete(self, request, email):
        try:
            user = Register.objects.get(email=email)
        except Register.DoesNotExist:
            return Response({'error': 'User not found.'}, status=404)

        if user.profile.photo_url:
            user.profile.photo_url.delete(save=False)
            user.profile.photo_url = None
            user.profile.save()
            return Response({'message': 'Profile photo deleted successfully.'}, status=200)
        else:
            return Response({'error': 'No profile photo to delete.'}, status=400)

# Wallet Amount
@api_view(['GET'])
def wallet_amount(request, email):
    try:
        user = Register.objects.get(email=email)
        profile = user.profile
    except (Register.DoesNotExist, Profile.DoesNotExist):
        return Response({'error': 'User or profile not found.'}, status=404)

    return Response({'wallet_amount': profile.wallet_amount}, status=200)

# Get Live Prices
@api_view(['GET'])
def get_live_prices(request):
    ids = request.GET.get('ids', 'bitcoin,ethereum,tether,dogecoin,solana,cardano')
    vs_currencies = request.GET.get('vs_currencies', 'usd')

    cache_key = f"live_prices_{ids}_{vs_currencies}"
    cached_data = cache.get(cache_key)

    if cached_data:
        return Response(cached_data)

    data = fetch_live_prices(ids, vs_currencies)
    if data:
        cache.set(cache_key, data, timeout=120)
        return Response(data)
    else:
        return Response({'error': 'Failed to fetch prices.'}, status=500)

# Purchase Tokens (For Purchase History Table)
@api_view(['POST'])
def purchase_tokens(request):
    email = request.data.get('email')
    coin = request.data.get('coin')
    quantity = int(request.data.get('quantity'))

    if not email or not coin or quantity < 1:
        return Response({'error': 'Invalid request.'}, status=400)

    try:
        user = Register.objects.get(email=email)
        profile = user.profile
    except (Register.DoesNotExist, Profile.DoesNotExist):
        return Response({'error': 'User or profile not found.'}, status=404)

    response = requests.get(
        "https://api.coingecko.com/api/v3/simple/price",
        params={'ids': coin.lower(), 'vs_currencies': 'usd'}
    )
    if response.status_code != 200:
        return Response({'error': 'Failed to fetch coin price.'}, status=500)

    price_data = response.json()
    if coin.lower() not in price_data:
        return Response({'error': 'Invalid coin selected.'}, status=400)

    price_per_token = Decimal(price_data[coin.lower()]['usd'])
    total_cost = price_per_token * quantity

    if profile.wallet_amount < total_cost:
        return Response({'error': 'Insufficient wallet balance.'}, status=400)

    profile.wallet_amount -= total_cost
    profile.save()

    # Update token balance
    balance, _ = TokenBalance.objects.get_or_create(user=user, coin=coin)
    balance.quantity += quantity
    balance.save()

    Transaction.objects.create(
        user=user,
        coin=coin,
        quantity=quantity,
        total_price=total_cost,
        type='buy'
    )

    return Response({
        'message': f'Purchased {quantity} {coin} token(s) for ${total_cost:.2f}',
        'wallet_amount': profile.wallet_amount
    }, status=200)

# Transaction 
@api_view(['GET'])
def user_transactions(request, email):
    try:
        user = Register.objects.get(email=email)
    except Register.DoesNotExist:
        return Response({'error': 'User not found.'}, status=404)

    transactions = user.transactions.all().order_by('-purchased_at')
    serializer = TransactionSerializer(transactions, many=True)
    return Response(serializer.data, status=200)

# Purchase Token Summary (For Total Purchased Tokens Table)
@api_view(['GET'])
def purchased_token_summary(request, email):
    try:
        user = Register.objects.get(email=email)
    except Register.DoesNotExist:
        return Response({'error': 'User not found.'}, status=404)

    transactions = Transaction.objects.filter(user=user, type='buy')

    summary = transactions.values('coin').annotate(
        total_tokens=Sum('quantity'),
        total_value=Sum('total_price')
    ).filter(total_tokens__gt=0).order_by('coin')

    for item in summary:
        item['total_value'] = round(item['total_value'], 2)

    return Response(summary)

# Sell Token 
@api_view(['POST'])
def sell_tokens(request):
    email = request.data.get('email')
    coin = request.data.get('coin')
    quantity = int(request.data.get('quantity'))

    if not email or not coin or quantity < 1:
        return Response({'error': 'Invalid request.'}, status=400)

    try:
        user = Register.objects.get(email=email)
        profile = user.profile
    except (Register.DoesNotExist, Profile.DoesNotExist):
        return Response({'error': 'User or profile not found.'}, status=404)

    try:
        balance = TokenBalance.objects.get(user=user, coin=coin)
    except TokenBalance.DoesNotExist:
        return Response({'error': f'No {coin} balance found for this user.'}, status=404)

    if balance.quantity < quantity:
        return Response({'error': f'Insufficient {coin} tokens to sell. You have {balance.quantity}.'}, status=400)

    response = requests.get(
        "https://api.coingecko.com/api/v3/simple/price",
        params={'ids': coin.lower(), 'vs_currencies': 'usd'}
    )
    if response.status_code != 200:
        return Response({'error': 'Failed to fetch coin price.'}, status=500)

    price_data = response.json()
    if coin.lower() not in price_data:
        return Response({'error': 'Invalid coin selected.'}, status=400)

    price_per_token = Decimal(price_data[coin.lower()]['usd'])
    total_sale_value = price_per_token * quantity

    profile.wallet_amount += total_sale_value
    profile.save()

    balance.quantity -= quantity
    balance.save()

    Transaction.objects.create(
        user=user,
        coin=coin,
        quantity=quantity,
        total_price=total_sale_value,
        type='sell'
    )

    return Response({
        'message': f'Sold {quantity} {coin} token(s) for ${total_sale_value:.2f}',
        'wallet_amount': profile.wallet_amount
    }, status=200)

# Token Balance
@api_view(['GET'])
def token_balances(request, email):
    try:
        user = Register.objects.get(email=email)
    except Register.DoesNotExist:
        return Response({'error': 'User not found.'}, status=404)

    balances = TokenBalance.objects.filter(user=user).order_by('coin')
    
    data = [
        {
            'coin': balance.coin,
            'quantity': balance.quantity
        }
        for balance in balances
    ]

    total_quantity = sum(item['quantity'] for item in data)

    response_data = {
        'balances': data,
        'total_quantity': total_quantity
    }

    return Response(response_data, status=200)

# User Sell Transaction
@api_view(['GET'])
def user_sell_transactions(request, email):
    try:
        user = Register.objects.get(email=email)
    except Register.DoesNotExist:
        return Response({'error': 'User not found.'}, status=404)

    transactions = user.transactions.filter(type='sell').order_by('-purchased_at')
    serializer = TransactionSerializer(transactions, many=True)
    return Response(serializer.data, status=200)

# Profit-Loss Summary
@api_view(['GET'])
def profit_loss_summary(request, email):
    try:
        user = Register.objects.get(email=email)
    except Register.DoesNotExist:
        return Response({'error': 'User not found.'}, status=404)

    COIN_GECKO_IDS = {
        'bitcoin': 'bitcoin',
        'ethereum': 'ethereum',
        'tether': 'tether',
        'dogecoin': 'dogecoin',
        'solana': 'solana',
        'cardano': 'cardano',
    }

    coins = Transaction.objects.filter(user=user).values_list('coin', flat=True).distinct()

    if not coins:
        return Response([])

    coin_ids = ','.join(
        COIN_GECKO_IDS.get(coin.lower())
        for coin in coins
        if COIN_GECKO_IDS.get(coin.lower())
    )

    price_data = {}
    if coin_ids:
        price_data = fetch_live_prices(coin_ids, 'usd')

    summary = []

    for coin in coins:
        purchases = Transaction.objects.filter(user=user, coin=coin, type='buy')
        total_purchased_quantity = purchases.aggregate(Sum('quantity'))['quantity__sum'] or 0
        total_invested = purchases.aggregate(Sum('total_price'))['total_price__sum'] or Decimal('0.00')

        sells = Transaction.objects.filter(user=user, coin=coin, type='sell')
        total_sold_quantity = sells.aggregate(Sum('quantity'))['quantity__sum'] or 0
        total_earned = sells.aggregate(Sum('total_price'))['total_price__sum'] or Decimal('0.00')

        holding_quantity = total_purchased_quantity - total_sold_quantity

        coin_id = COIN_GECKO_IDS.get(coin.lower())
        current_price = Decimal(price_data.get(coin_id, {}).get('usd', 0)) if coin_id else Decimal('0')

        holding_amount = holding_quantity * current_price

        profit_loss = (total_earned + holding_amount) - total_invested
        profit_loss = profit_loss.quantize(Decimal('0.01'))
        if abs(profit_loss) < Decimal('0.01'):
            profit_loss = Decimal('0.00')

        ProfitLossSummary.objects.update_or_create(
            user=user,
            coin=coin,
            defaults={
                'total_purchased_quantity': total_purchased_quantity,
                'total_invested': total_invested,
                'total_sold_quantity': total_sold_quantity,
                'total_earned': total_earned,
                'holding_quantity': holding_quantity,
                'current_price': current_price,
                'holding_amount': holding_amount,
                'net_profit_loss': profit_loss
            }
        )

        summary.append({
            'coin': coin,
            'total_purchased_quantity': total_purchased_quantity,
            'total_invested': round(total_invested, 2),
            'total_sold_quantity': total_sold_quantity,
            'total_earned': round(total_earned, 2),
            'holding_quantity': holding_quantity,
            'current_price': round(current_price, 2),
            'holding_amount': round(holding_amount, 2),
            'net_profit_loss': profit_loss,
        })

        summary.sort(key=lambda x: x['coin'].lower())

    return Response(summary)
