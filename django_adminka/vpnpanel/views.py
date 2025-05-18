from unfold.views import UnfoldModelAdminViewMixin
from .forms import BotSendForm, AddKeyForm, DeleteAllKeysForm, ExtendKeyForm, AddServerForm, GetConfigFilesForm, TransferClientsForm
from django.views.generic import FormView
from django.contrib import messages
from datetime import datetime, timedelta, timezone
import time
from django.conf import settings
from django.http import HttpResponse
from .models import User, ClientAsKey, Server
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
                messages.error(request, f'Пользователя с telegram_id {data["telegram_id"]} нет в базе даных' )
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
            return redirect(reverse('admin:vpnpanel_clientaskey_changelist')+ f'?telegram_id={data["telegram_id"]}')
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
                messages.error(request, f'Пользователя с telegram_id {data["telegram_id"]} нет в базе даных' )
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
            return redirect(reverse('admin:vpnpanel_clientaskey_changelist')+ f'?telegram_id={data["telegram_id"]}')
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
        
class AddServerView(UnfoldModelAdminViewMixin, FormView):
    title = "Добавить сервер"
    template_name = "admin/add_server.html"
    permission_required = ()
    form_class = AddServerForm

    def post(self, request, *args, **kwargs):
        form = AddServerForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            try:
                response = requests.post(f"http://{settings.MANAGER_SERVER_HOST}:{settings.MANAGER_SERVER_PORT}/add_server", json=data)
                response.raise_for_status()
                messages.success(request, "Сервер успешно отправлен на обработку!")
            except requests.RequestException as e:
                try:
                    error_detail = response.json().get('detail', str(e))
                except Exception:
                    error_detail = str(e)
                messages.error(request, f"Ошибка при отправке: {error_detail}")
                return redirect('/admin/')
            return redirect(reverse("admin:vpnpanel_server_changelist"))
        else:
            return self.form_invalid(form)
        
class GetConfigFilesView(UnfoldModelAdminViewMixin, FormView):
    title = "Выгрузить файл конфигурации"
    template_name = "admin/export_config.html"
    permission_required = ()
    form_class = GetConfigFilesForm

    def post(self, request, *args, **kwargs):
        form = GetConfigFilesForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data

            try:
                server = Server.objects.get(host=data['host'], created=1)
            except Server.DoesNotExist:
                messages.error(request, f'Сервера {data["host"]} нет в базе')
                return redirect(reverse("admin:vpnpanel_server_changelist"))

            try:
                response = requests.get(f"http://{settings.MANAGER_SERVER_HOST}:{settings.MANAGER_SERVER_PORT}/export-config?host={data['host']}&username={server.username}&password={server.password}&port={server.port}")
                if response.status_code == 200:
                    django_response = HttpResponse(
                        response.iter_content(chunk_size=8192),
                        content_type=response.headers.get('content-type', 'application/octet-stream')
                    )
                    django_response['Content-Disposition'] = response.headers.get('content-disposition', f'attachment; filename="{data["host"]}_config.yaml"')
                    return django_response
            except requests.RequestException as e:
                try:
                    error_detail = response.json().get('detail', str(e))
                except Exception:
                    error_detail = str(e)
                messages.error(request, f"Ошибка при отправке: {error_detail}")
                return redirect('/admin/')
            return redirect(reverse("admin:vpnpanel_server_changelist"))
        else:
            return self.form_invalid(form)

class TransferClientsFromServerToServerView(UnfoldModelAdminViewMixin, FormView):
    title = "Перенести клиентов"
    template_name = "admin/transfer_clients.html"
    permission_required = ()
    form_class = TransferClientsForm

    def post(self, request, *args, **kwargs):
        form = TransferClientsForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data

            try:
                server_from = Server.objects.get(host=data['host_from'], created=1)
            except Server.DoesNotExist:
                messages.error(request, f'Сервера {data["host_from"]} нет в базе')
                return redirect(reverse("admin:vpnpanel_server_changelist"))

            try:
                server_to = Server.objects.get(host=data['host_to'], created=1)
            except Server.DoesNotExist:
                messages.error(request, f'Сервера {data["host_to"]} нет в базе')
                return redirect(reverse("admin:vpnpanel_server_changelist"))
            
            try:
                url = (
                    f"http://{settings.MANAGER_SERVER_HOST}:{settings.MANAGER_SERVER_PORT}/transfer-clients?"
                    f"host_to={data['host_to']}&"
                    f"password_to={server_to.password}&"
                    f"username_to={server_to.username}&"
                    f"port_to={server_to.port}&"
                    f"host_from={data['host_from']}&"
                    f"password_from={server_from.password}&"
                    f"username_from={server_from.username}&"
                    f"port_from={server_from.port}"
                )
                response = requests.get(url)
                if response.status_code == 200:
                    ClientAsKey.objects.filter(host=data['host_from']).update(host=data['host_to'], public_key=server_to.public_key)
                    messages.success(request, f"Клиенты перенесены!")
                    return redirect(reverse("admin:vpnpanel_server_changelist"))
            except requests.RequestException as e:
                try:
                    error_detail = response.json().get('detail', str(e))
                except Exception:
                    error_detail = str(e)
                messages.error(request, f"Ошибка при отправке: {error_detail}")
                return redirect('/admin/')
            return redirect(reverse("admin:vpnpanel_server_changelist"))
            
        else:
            return self.form_invalid(form)