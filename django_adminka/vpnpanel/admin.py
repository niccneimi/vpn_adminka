from django.contrib import admin
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from .models import Server, Order, User
from .forms import AddServerForm, BotSendForm
from datetime import datetime
import requests

original_get_urls = admin.site.get_urls

def bot_send_view(request):
    if request.method == 'POST':
        form = BotSendForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            users = User.objects.all()
            TELEGRAM_TOKEN = settings.TELEGRAM_BOT_TOKEN
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            try:
                for user in users:
                    response = requests.post(
                        url,
                        data={
                            'chat_id': user.user_id,
                            'text': data['message'],
                            'parse_mode': 'HTML'
                        }
                    )
                    response.raise_for_status()
            except requests.RequestException as e:
                messages.error(request, f"Ошибка соединения: {str(e)}")
            messages.success(request, "Рассылка завершена!")
            return redirect(request.path)
    else:
        form = BotSendForm()
    return render(request, 'admin/bot_sending.html', {'form': form})

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
        path('bot-sending/',admin.site.admin_view(bot_send_view) ,name='bot-sending')
    ]
    return custom_urls + urls
admin.site.get_urls = get_urls

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
    
