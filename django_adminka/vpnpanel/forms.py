from django import forms
from unfold.widgets import UnfoldAdminTextareaWidget

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
    telegram_id = forms.CharField(max_length=255)
    host = forms.CharField(max_length=255, required=False)
    uuid = forms.CharField(max_length=255, required=False)
    email = forms.EmailField(required=False)
    public_key = forms.CharField(max_length=255, required=False)
    expiration_date = forms.IntegerField(required=False, help_text="Unix timestamp")

# Форма для продления подписки
class ExtendSubscriptionForm(forms.Form):
    user_id = forms.IntegerField(widget=forms.HiddenInput())
    days = forms.IntegerField(min_value=1, label="Количество дней продления")

# Форма для изменения статуса тестового периода
class ChangeFreeTrialStatusForm(forms.Form):
    user_id = forms.IntegerField(widget=forms.HiddenInput())
    free_trial_used = forms.IntegerField(min_value=0, max_value=1, label="Использован тестовый период (0 или 1)")