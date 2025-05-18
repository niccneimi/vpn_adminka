from django import forms
from unfold.widgets import UnfoldAdminTextareaWidget, UnfoldAdminTextInputWidget, UnfoldAdminIntegerFieldWidget

# Форма для добавления vpn сервера
class AddServerForm(forms.Form):
    host = forms.CharField(max_length=255, label="Host")
    port = forms.IntegerField(initial=22, label="Port")
    username = forms.CharField(max_length=255, label="Username")
    password = forms.CharField(max_length=255, label="Password", widget=forms.PasswordInput)
    location = forms.CharField(max_length=255, label="Location")

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