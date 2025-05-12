from django.contrib import admin
from django.urls import path
from django import forms
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Server, Order
from datetime import datetime
import requests

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

def get_urls():
    urls = original_get_urls()
    custom_urls = [
        path('financial-report/', admin.site.admin_view(financial_report_view), name='financial-report'),
    ]
    return custom_urls + urls
admin.site.get_urls = get_urls

class AddServerForm(forms.Form):
    host = forms.CharField(max_length=255, label="Host")
    port = forms.IntegerField(initial=22, label="Port")
    username = forms.CharField(max_length=255, label="Username")
    password = forms.CharField(max_length=255, label="Password", widget=forms.PasswordInput)
    location = forms.CharField(max_length=255, label="Location")

@admin.register(Server)
class ServersAdmin(admin.ModelAdmin):
    list_display = ('host', 'port', 'username', 'password', 'location', 'clients_on_server', 'created_at')
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('add-server/', self.admin_site.admin_view(self.add_server_view), name='add-server-custom'),
        ]
        return custom_urls + urls

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
    
