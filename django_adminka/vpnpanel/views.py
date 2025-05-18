from unfold.views import UnfoldModelAdminViewMixin
from .forms import BotSendForm
from django.views.generic import FormView
from django.contrib import messages
from django.conf import settings
from .models import User
import requests

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