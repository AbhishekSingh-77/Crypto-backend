from django.contrib import admin
from .models import Register, Profile, Transaction, TokenBalance, ProfitLossSummary

admin.site.register(Register)
admin.site.register(Profile)

@admin.register(TokenBalance)
class TokenBalanceAdmin(admin.ModelAdmin):
    list_display = ('user', 'coin', 'quantity', 'updated_at')
    search_fields = ('user__username', 'coin')
    list_filter = ('user__username', 'coin',)
    ordering = ('-updated_at',)
    date_hierarchy = 'updated_at'

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'coin', 'type', 'quantity', 'total_price', 'purchased_at')
    search_fields = ('user__username', 'type')
    list_filter = ('user__username', 'type', 'purchased_at')
    ordering = ('-purchased_at',)
    date_hierarchy = 'purchased_at'

@admin.register(ProfitLossSummary)
class ProfitLossSummaryAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'coin', 'total_purchased_quantity', 'total_invested',
        'total_sold_quantity', 'total_earned', 'holding_quantity',
        'current_price', 'holding_amount', 'net_profit_loss', 'last_updated'
    )
    search_fields = ('user__username', 'coin')
    list_filter = ('user__username', 'coin', 'last_updated')
    ordering = ('-last_updated',)
    date_hierarchy = 'last_updated'
