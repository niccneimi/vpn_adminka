from django import forms

class AddServerForm(forms.Form):
    host = forms.CharField(max_length=255, label="Host")
    port = forms.IntegerField(initial=22, label="Port")
    username = forms.CharField(max_length=255, label="Username")
    password = forms.CharField(max_length=255, label="Password", widget=forms.PasswordInput)
    location = forms.CharField(max_length=255, label="Location")

class BotSendForm(forms.Form):
    message = forms.CharField(label='Сообщение', widget=forms.Textarea)