from django import forms
from unfold.widgets import UnfoldAdminTextareaWidget, UnfoldAdminTextInputWidget, UnfoldAdminIntegerFieldWidget, UnfoldAdminPasswordInput

# Форма для добавления vpn сервера
class AddServerForm(forms.Form):
    host = forms.CharField(max_length=255, required=True, label="Хост", widget=UnfoldAdminTextInputWidget())
    port = forms.IntegerField(initial=22, label="Порт", widget=UnfoldAdminIntegerFieldWidget())
    username = forms.CharField(initial="root", max_length=255, label="Имя пользователя", widget=UnfoldAdminTextInputWidget())
    password = forms.CharField(max_length=255, label="Пароль", widget=UnfoldAdminPasswordInput)
    location = forms.CharField(max_length=255, label="Локация", widget=UnfoldAdminTextInputWidget(attrs={'placeholder': 'Используйте одинаковое форматирование (UPPERCASE) для одних локаций (NL, FR)'}))

# Форма для рассылки в боте
class BotSendForm(forms.Form):
    message = forms.CharField(label="Сообщение", widget=UnfoldAdminTextareaWidget(attrs={'placeholder': 'Введите сообщение'}))

# Форма для добавления ключа
class AddKeyForm(forms.Form):
    telegram_id = forms.CharField(label="Telegram ID", required=True, widget=UnfoldAdminTextInputWidget())
    days_count = forms.IntegerField(label="Количество дней", min_value=1, required=True, widget=UnfoldAdminIntegerFieldWidget())

# Форма для удаления всех ключей пользователю
class DeleteAllKeysForm(forms.Form):
    telegram_id = forms.CharField(label="Telegram ID", required=True, widget=UnfoldAdminTextInputWidget())

# Форма для продления подписки
class ExtendKeyForm(forms.Form):
    key_uuid = forms.CharField(label="UUID ключа", required=True, widget=UnfoldAdminTextInputWidget())
    days_count = forms.IntegerField(label="Количество дней", min_value=1, required=True, widget=UnfoldAdminIntegerFieldWidget())

# Форма для получения файлов конфигурации с клиентами
class GetConfigFilesForm(forms.Form):
    host = forms.CharField(label="Хост сервера", required=True, widget=UnfoldAdminTextInputWidget())