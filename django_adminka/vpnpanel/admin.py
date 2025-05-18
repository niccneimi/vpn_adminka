from django.contrib import admin
from unfold.admin import ModelAdmin
from django.urls import path, reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.html import format_html
from django.contrib import messages
from django.conf import settings
from .models import Server, Order, User, ClientAsKey
from .forms import AddServerForm, AddKeyForm, ExtendSubscriptionForm, ChangeFreeTrialStatusForm
from .views import BotSendView, AddKeyView
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

        return [
            path(
                "bot-sending/", botsendview, name="vpnpanel_user_bot_sending"
            ),
            path(
                "add-key/", addkeyview, name="vpnpanel_user_add_key"
            ),
        ] + super().get_urls() 
    
    # Представления для кастомных действий
    # def add_key_view(self, request, user_id):
    #     user = get_object_or_404(User, pk=user_id)
    #     if request.method == 'POST':
    #         form = AddKeyForm(request.POST)
    #         if form.is_valid():
    #             data = form.cleaned_data
    #             ClientAsKey.objects.create(
    #                 telegram_id=data['telegram_id'],
    #                 host=data.get('host'),
    #                 uuid=data.get('uuid'),
    #                 email=data.get('email'),
    #                 public_key=data.get('public_key'),
    #                 expiration_date=data.get('expiration_date') or 0,
    #                 deleted=0,
    #             )
    #             messages.success(request, f"Ключ успешно добавлен пользователю {user_id}")
    #             return redirect(f'../../')
    #     else:
    #         form = AddKeyForm(initial={'telegram_id': user_id})
    #     context = dict(
    #         self.admin_site.each_context(request),
    #         form=form,
    #         user=user,
    #         title=f"Добавить ключ пользователю {user_id}"
    #     )
    #     return render(request, 'admin/add_key_form.html', context)

    def delete_keys_view(self, request, user_id):
        if request.method == 'POST':
            deleted_count, _ = ClientAsKey.objects.filter(telegram_id=str(user_id)).delete()
            messages.success(request, f"Удалено {deleted_count} ключей пользователя {user_id}")
            return redirect(f'../../')
        context = dict(
            self.admin_site.each_context(request),
            user_id=user_id,
            title=f"Удалить все ключи пользователя {user_id}"
        )
        return render(request, 'admin/confirm_delete_keys.html', context)

    def change_trial_status_view(self, request, user_id):
        user = get_object_or_404(User, pk=user_id)
        if request.method == 'POST':
            form = ChangeFreeTrialStatusForm(request.POST)
            if form.is_valid():
                user.free_trial_used = form.cleaned_data['free_trial_used']
                user.save()
                messages.success(request, f"Статус тестового периода изменен для пользователя {user_id}")
                return redirect(f'../../')
        else:
            form = ChangeFreeTrialStatusForm(initial={'user_id': user_id, 'free_trial_used': user.free_trial_used})
        context = dict(
            self.admin_site.each_context(request),
            form=form,
            user=user,
            title=f"Изменить статус тестового периода пользователя {user_id}"
        )
        return render(request, 'admin/change_trial_status_form.html', context)

    def extend_subscription_view(self, request, user_id):
        user = get_object_or_404(User, pk=user_id)
        if request.method == 'POST':
            form = ExtendSubscriptionForm(request.POST)
            if form.is_valid():
                days = form.cleaned_data['days']
                # Получаем последний заказ, чтобы продлить expiration_date
                last_order = Order.objects.filter(user=user).order_by('-expiration_date').first()
                if last_order and last_order.expiration_date:
                    new_expiration = last_order.expiration_date + days * 86400
                    last_order.expiration_date = new_expiration
                    last_order.save()
                    messages.success(request, f"Подписка продлена на {days} дней для пользователя {user_id}")
                else:
                    messages.error(request, "Не найден заказ для продления подписки")
                return redirect(f'../../')
        else:
            form = ExtendSubscriptionForm(initial={'user_id': user_id})
        context = dict(
            self.admin_site.each_context(request),
            form=form,
            user=user,
            title=f"Продлить подписку пользователя {user_id}"
        )
        return render(request, 'admin/extend_subscription_form.html', context)
    
@admin.register(ClientAsKey)
class ClientAsKeyAdmin(ModelAdmin):
    list_display = ('telegram_id', 'host', 'uuid', 'created_at')
    ordering = ('-created_at',)