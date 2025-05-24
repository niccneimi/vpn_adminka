from django.contrib import admin
from unfold.admin import ModelAdmin
from django.urls import path, reverse
from django.shortcuts import render
from django.utils.html import format_html
from .models import Server, Order, User, ClientAsKey, Tarif
from .views import BotSendView, AddKeyView, DeleteAllKeysView, ExtendKeyView, AddServerView, GetConfigFilesView, TransferClientsFromServerToServerView
from .views_statistics import StatisticsHomeView, UsersStatisticsView, ServersStatisticsView, ClientAccessLogsView, TimeReportsView
from datetime import datetime

original_get_urls = admin.site.get_urls

def get_urls():
    url_patterns = original_get_urls()
    
    url_patterns += [
        path('financial-report/', admin.site.admin_view(financial_report_view), name='financial_report'),
    ]
    
    url_patterns += [
        path('statistics/', admin.site.admin_view(StatisticsHomeView.as_view()), name='statistics_home'),
        path('statistics/users/', admin.site.admin_view(UsersStatisticsView.as_view()), name='statistics_users'),
        path('statistics/servers/', admin.site.admin_view(ServersStatisticsView.as_view()), name='statistics_servers'),
        path('statistics/client-logs/<str:uuid>/', admin.site.admin_view(ClientAccessLogsView.as_view()), name='statistics_client_logs'),
        path('statistics/time-reports/<str:period>/', admin.site.admin_view(TimeReportsView.as_view()), name='statistics_time_reports'),
        path('statistics/time-reports/', admin.site.admin_view(TimeReportsView.as_view()), name='statistics_time_reports_default'),
    ]
    
    return url_patterns

admin.site.get_urls = get_urls

def financial_report_view(request):
    orders = Order.objects.order_by('-created_at')

    report_data = []
    for order in orders:
        user_id_str = str(order.user.user_id)
        user_name = order.user.name or ""
        promocode_used = getattr(order, 'promocode_used', None)
        package_period = getattr(order, 'package_size', None)
        expiration_date = getattr(order, 'expiration_date', None)
        package_end_date = datetime.fromtimestamp(expiration_date) if expiration_date else None
        transaction_hash = order.extra.get('hash_tx') if order.extra else None

        report_data.append({
            'purchase_date': order.created_at,
            'currency': order.currency,
            'package_end_date': package_end_date,
            'transaction_hash': transaction_hash,
            'telegram_id': user_id_str,
            'user_name': user_name,
            'package_period': package_period,
            'used_promocode': promocode_used,
        })

    context = dict(
        admin.site.each_context(request),
        report_data=report_data,
    )
    return render(request, "admin/financial_report.html", context)

@admin.register(Server)
class ServersAdmin(ModelAdmin):
    list_display = ('host', 'port', 'username', 'password', 'location', 'clients_on_server', 'created_at')

    def get_urls(self):
        addserverview = self.admin_site.admin_view(AddServerView.as_view(model_admin=self))
        exportconfigview = self.admin_site.admin_view(GetConfigFilesView.as_view(model_admin=self))
        tranferclientsview = self.admin_site.admin_view(TransferClientsFromServerToServerView.as_view(model_admin=self)) 

        custom_urls = [
            path(
                'add-server/', addserverview, name='vpnpanel_server_add_server'
            ),
            path(
                'export-config/', exportconfigview, name='vpnpanel_server_export_config'
            ),
            path(
                'tranfer-clients', tranferclientsview, name='vpnpanel_server_transfer_clients'
            )
        ]
        return custom_urls + super().get_urls()

@admin.register(User)
class UserAdmin(ModelAdmin):
    list_display = ('user_id_with_name', 'lang', 'free_trial_used', 'created_at', 'keys_link')
    list_filter = ('free_trial_used',)
    search_fields = ('user_id', 'name')
    ordering = ('-created_at',)
    
    def user_id_with_name(self, obj):
        if obj.name:
            return f"{obj.user_id} ({obj.name})"
        return obj.user_id
    user_id_with_name.short_description = 'Telegram ID (Username)'
    user_id_with_name.admin_order_field = 'user_id'

    def keys_link(self, obj):
        url = (
            reverse('admin:vpnpanel_clientaskey_changelist')
            + f'?telegram_id={obj.user_id}'
        )
        return format_html('<a href="{}">Перейти к ключам</a>', url)
    keys_link.short_description = 'Ключи пользователя'

    def get_urls(self):
        botsendview = self.admin_site.admin_view(BotSendView.as_view(model_admin=self))
        addkeyview = self.admin_site.admin_view(AddKeyView.as_view(model_admin=self))
        deleteallkeysview = self.admin_site.admin_view(DeleteAllKeysView.as_view(model_admin=self))
        extendkeyview = self.admin_site.admin_view(ExtendKeyView.as_view(model_admin=self))
        return [
            path(
                "bot-sending/", botsendview, name="vpnpanel_user_bot_sending"
            ),
            path(
                "add-key/", addkeyview, name="vpnpanel_user_add_key"
            ),
            path(
                "delete-all-keys/", deleteallkeysview, name="vpnpanel_user_delete_all_keys"
            ),
            path(
                "extend-key/", extendkeyview, name="vpnpanel_user_extend_key"
            )
        ] + super().get_urls() 
    
@admin.register(ClientAsKey)
class ClientAsKeyAdmin(ModelAdmin):
    list_display = ('telegram_id_with_name', 'host', 'uuid', 'created_at', 'formatted_expiration_date', 'deleted', 'logs_link')
    list_filter = ('deleted',)
    ordering = ('-created_at',)
    search_fields = ('telegram_id', 'user__name', 'uuid')
    
    def telegram_id_with_name(self, obj):
        try:
            user = User.objects.get(user_id=obj.telegram_id)
            if user.name:
                return f"{obj.telegram_id} ({user.name})"
        except User.DoesNotExist:
            pass
        return obj.telegram_id
    telegram_id_with_name.short_description = 'Telegram ID (Username)'
    telegram_id_with_name.admin_order_field = 'telegram_id'

    def logs_link(self, obj):
        url = reverse('admin:statistics_client_logs', args=[obj.uuid])
        return format_html('<a href="{}">Просмотр логов</a>', url)
    logs_link.short_description = 'Логи доступа'

    def formatted_expiration_date(self, obj):
        if obj.expiration_date:
            dt = datetime.fromtimestamp(obj.expiration_date)
            formatted = dt.strftime('%b %d, %Y, %-I:%M %p')
            formatted = formatted.replace('AM', 'a.m.').replace('PM', 'p.m.')
            return formatted
        return '-'
    formatted_expiration_date.short_description = 'Дата истечения'

@admin.register(Tarif)
class TarifsAdmin(ModelAdmin):
    list_display = ('price', 'days')

@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = (
        'user_display',
        'amount_formatted',
        'currency',
        'hash_tx',
        'expiration_date_formatted',
        'package_size',
        'promocode_used',
        'created_at',
    )
    search_fields = ('user__user_id', 'user__name', 'extra__hash_tx')

    def user_display(self, obj):
        if hasattr(obj.user, 'user_id'):
            if obj.user.name:
                return f"{obj.user.user_id} ({obj.user.name})"
            return str(obj.user.user_id)
        return str(obj.user)
    user_display.short_description = 'Telegram ID (Username)'
    user_display.admin_order_field = 'user'

    def amount_formatted(self, obj):
        return f"{obj.amount:.8f}"
    amount_formatted.short_description = 'Amount'
    amount_formatted.admin_order_field = 'amount'

    def hash_tx(self, obj):
        if obj.extra and isinstance(obj.extra, dict):
            return obj.extra.get('hash_tx', '-')
        return '-'
    hash_tx.short_description = 'Transaction Hash'

    def expiration_date_formatted(self, obj):
        if obj.expiration_date:
            return datetime.fromtimestamp(obj.expiration_date).strftime('%b %d, %Y, %I:%M %p').replace('AM', 'a.m.').replace('PM', 'p.m.')
        return '-'
    expiration_date_formatted.short_description = 'Expiration Date'
    expiration_date_formatted.admin_order_field = 'expiration_date'