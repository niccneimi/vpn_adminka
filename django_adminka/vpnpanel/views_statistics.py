from django.views.generic import TemplateView
from unfold.views import UnfoldModelAdminViewMixin
from .statistics import (
    get_users_statistics, get_servers_statistics, 
    get_client_access_logs, get_time_period_data
)
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import ClientAsKey
from django.shortcuts import get_object_or_404
from django.http import Http404
from django.contrib import admin

class AdminViewMixin(LoginRequiredMixin):
    """Миксин для добавления контекста админки."""
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(admin.site.each_context(self.request))
        
        # Добавляем основные переменные админ-контекста
        context['has_permission'] = True
        context['is_popup'] = False
        context['is_nav_sidebar_enabled'] = True
        context['available_apps'] = admin.site.get_app_list(self.request)
        
        return context

@method_decorator(staff_member_required, name='dispatch')
class StatisticsHomeView(AdminViewMixin, TemplateView):
    template_name = 'admin/statistics/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Общая статистика"
        context['user_stats'] = get_users_statistics()
        context['server_stats'] = get_servers_statistics()
        context['day_stats'] = get_time_period_data('day')
        context['week_stats'] = get_time_period_data('week')
        context['month_stats'] = get_time_period_data('month')
        return context

@method_decorator(staff_member_required, name='dispatch')
class UsersStatisticsView(AdminViewMixin, TemplateView):
    template_name = 'admin/statistics/users.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Статистика пользователей"
        context['user_stats'] = get_users_statistics()
        return context

@method_decorator(staff_member_required, name='dispatch')
class ServersStatisticsView(AdminViewMixin, TemplateView):
    template_name = 'admin/statistics/servers.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Статистика серверов"
        context['server_stats'] = get_servers_statistics()
        return context

@method_decorator(staff_member_required, name='dispatch')
class ClientAccessLogsView(AdminViewMixin, TemplateView):
    template_name = 'admin/statistics/client_logs.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Логи доступа клиента"
        uuid = self.kwargs.get('uuid')
        
        if not uuid:
            raise Http404("UUID не указан")
        
        client_data = get_client_access_logs(uuid)
        if not client_data:
            raise Http404("Клиент не найден")
            
        context['client_data'] = client_data
        return context

@method_decorator(staff_member_required, name='dispatch')
class TimeReportsView(AdminViewMixin, TemplateView):
    template_name = 'admin/statistics/time_reports.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Отчеты по периодам"
        period = self.kwargs.get('period', 'day')
        
        if period not in ['day', 'week', 'month']:
            period = 'day'
            
        context['period'] = period
        context['period_data'] = get_time_period_data(period)
        return context 