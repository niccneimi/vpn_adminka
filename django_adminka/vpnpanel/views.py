from unfold.views import UnfoldModelAdminViewMixin
from .forms import BotSendForm, AddKeyForm, DeleteAllKeysForm, ExtendKeyForm
from django.views.generic import FormView
from django.contrib import messages
from datetime import datetime, timedelta, timezone
import time
from django.conf import settings
from .models import User, ClientAsKey
import requests
from django.urls import reverse

from django.shortcuts import redirect

class BotSendView(UnfoldModelAdminViewMixin, FormView):
    title = "Рассылка в Telegram"
    template_name = "admin/bot_sending.html"
    permission_required = ()
    form_class = BotSendForm

    def post(self, request, *args, **kwargs):
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
        return redirect('/admin/')
    
class AddKeyView(UnfoldModelAdminViewMixin, FormView):
    title = "Добавить ключ"
    template_name = "admin/add_new_key.html"
    permission_required = ()
    form_class = AddKeyForm

    def post(self, request, *args, **kwargs):
        form = AddKeyForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            try:
                user = User.objects.get(user_id=data['telegram_id'])
            except User.DoesNotExist:
                messages.error(request, f'Пользователя с telegram_id {data['telegram_id']} нет в базе даных' )
                return redirect('/admin/')

            if data['days_count'] < 1:
                messages.error(request, f'Количество дней должно быть больше 1' )
                return redirect('/admin/')
            
            try:
                data = {
                    "telegram_id": str(data['telegram_id']),
                    "expiration_date": int((datetime.now(timezone.utc) + timedelta(days=data['days_count'])).timestamp())
                }
                create_user = requests.post(f"http://{settings.MANAGER_SERVER_HOST}:{settings.MANAGER_SERVER_PORT}/create_config", json=data)
                create_user.raise_for_status()
                if create_user.status_code != 200:
                    messages.error(request, f"Ошибка создания конфигурации: {create_user.text}")
                    return redirect('/admin/')
            except requests.RequestException as e:
                messages.error(request, f"Ошибка соединения c сервером менеджером: {str(e)}")
                return redirect('/admin/')
            messages.success(request, f"Новый ключ {create_user.json()['result'][0]['uuid']} успешно добавлен пользователю {data['telegram_id']}!")
            return redirect(reverse('admin:vpnpanel_clientaskey_changelist')+ f'?telegram_id={data['telegram_id']}')
        else:
            return self.form_invalid(form)
        
class DeleteAllKeysView(UnfoldModelAdminViewMixin, FormView):
    title = "Удалить все ключи пользователя"
    template_name = "admin/delete_all_keys.html"
    permission_required = ()
    form_class = DeleteAllKeysForm

    def post(self, request, *args, **kwargs):
        form = DeleteAllKeysForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            try:
                user = User.objects.get(user_id=data['telegram_id'])
            except User.DoesNotExist:
                messages.error(request, f'Пользователя с telegram_id {data['telegram_id']} нет в базе даных' )
                return redirect('/admin/')   
            expired_timestamp = int(time.mktime((datetime.now() - timedelta(days=1)).timetuple()))
            ClientAsKey.objects.filter(telegram_id=data['telegram_id']).update(expiration_date=expired_timestamp)
            try:
                response = requests.get(f"http://{settings.MANAGER_SERVER_HOST}:{settings.MANAGER_SERVER_PORT}/delete_expired")
                response.raise_for_status()
            except requests.RequestException as e:
                messages.error(request, f"Ошибка соединения c сервером менеджером: {str(e)}")
                return redirect('/admin/')
            messages.success(request, f"Все ключи успешно удалены пользователю {data['telegram_id']}!")
            return redirect(reverse('admin:vpnpanel_clientaskey_changelist')+ f'?telegram_id={data['telegram_id']}')
        else:
            return self.form_invalid(form)
        
class ExtendKeyView(UnfoldModelAdminViewMixin, FormView):
    title = "Продлить ключ"
    template_name = "admin/extend_key.html"
    permission_required = ()
    form_class = ExtendKeyForm

    def post(self, request, *args, **kwargs):
        form = ExtendKeyForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            try:
                key = ClientAsKey.objects.get(uuid=data['key_uuid'], deleted=0)
            except ClientAsKey.DoesNotExist:
                messages.error(request, f'Ключа с uuid {data["key_uuid"]} нет в базе или он удалён из неё')
                return redirect('/admin/')
            
            if data['days_count'] < 1:
                messages.error(request, f'Количество дней должно быть больше 1' )
                return redirect('/admin/')
            ClientAsKey.objects.filter(uuid=data['key_uuid'], deleted=0).update(expiration_date=(key.expiration_date + data['days_count'] * 24 * 60 * 60))
            messages.success(request, f"Ключ {key.uuid} успешно продлён пользователю {key.telegram_id} на {data['days_count']} дней!")
            return redirect(reverse('admin:vpnpanel_clientaskey_changelist')+ f'?telegram_id={key.telegram_id}')
        else:
            return self.form_invalid(form)