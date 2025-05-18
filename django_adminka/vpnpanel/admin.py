from django.contrib import admin
from unfold.admin import ModelAdmin
from django.urls import path, reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.html import format_html
from django.contrib import messages
from .models import Server, Order, User, ClientAsKey
from .forms import AddServerForm
from .views import BotSendView, AddKeyView, DeleteAllKeysView, ExtendKeyView, AddServerView
from datetime import datetime
import requests
from django.db.models import Max

original_get_urls = admin.site.get_urls
    
def financial_report_view(request):
    orders = Order.objects.order_by('-created_at')

    report_data = []
    for order in orders:
        user_id_str = str(order.user.user_id)
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
        custom_urls = [
            path(
                'add-server/', addserverview, name='vpnpanel_server_add_server'
            ),
        ]
        return custom_urls + super().get_urls()

    def add_server_view(self, request):
        if request.method == 'POST':
            form = AddServerForm(request.POST)
            if form.is_valid():
                data = form.cleaned_data
                try:
                    response = requests.post("http://localhost:8081/add_server", json=data)
                    response.raise_for_status()
                    messages.success(request, "Сервер успешно отправлен на обработку!")
                except requests.RequestException as e:
                    try:
                        error_detail = response.json().get('detail', str(e))
                    except Exception:
                        error_detail = str(e)
                    messages.error(request, f"Ошибка при отправке: {error_detail}")
                return redirect(request.path)
        else:
            form = AddServerForm()
        return render(request, 'admin/add_server_form.html', {'form': form})

@admin.register(User)
class UserAdmin(ModelAdmin):
    list_display = ('user_id', 'lang', 'free_trial_used', 'created_at', 'keys_link')
    list_filter = ('free_trial_used',)
    search_fields = ('user_id', 'name')
    ordering = ('-created_at',)

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
class ClientAsKeyAdmin(admin.ModelAdmin):
    list_display = ('telegram_id', 'host', 'uuid', 'created_at', 'formatted_expiration_date', 'deleted')
    ordering = ('-created_at',)

    def formatted_expiration_date(self, obj):
        if obj.expiration_date:
            dt = datetime.fromtimestamp(obj.expiration_date)
            formatted = dt.strftime('%b %d, %Y, %-I:%M %p')
            formatted = formatted.replace('AM', 'a.m.').replace('PM', 'p.m.')
            return formatted
        return '-'
    formatted_expiration_date.short_description = 'Дата истечения'