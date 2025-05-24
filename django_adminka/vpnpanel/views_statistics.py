from django.views.generic import TemplateView
from unfold.views import UnfoldModelAdminViewMixin
from .statistics import (
    get_users_statistics, get_servers_statistics, 
    get_client_access_logs, get_time_period_data
)
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from .models import ClientAsKey
from django.shortcuts import get_object_or_404
from django.http import Http404
from django.contrib import admin

@method_decorator(staff_member_required, name='dispatch')
class StatisticsHomeView(UnfoldModelAdminViewMixin, TemplateView):
    template_name = 'admin/statistics/home.html'
    title = "Общая статистика"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(admin.site.each_context(self.request))
        context['user_stats'] = get_users_statistics()
        context['server_stats'] = get_servers_statistics()
        context['day_stats'] = get_time_period_data('day')
        context['week_stats'] = get_time_period_data('week')
        context['month_stats'] = get_time_period_data('month')
        return context

@method_decorator(staff_member_required, name='dispatch')
class UsersStatisticsView(UnfoldModelAdminViewMixin, TemplateView):
    template_name = 'admin/statistics/users.html'
    title = "Статистика пользователей"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(admin.site.each_context(self.request))
        context['user_stats'] = get_users_statistics()
        return context

@method_decorator(staff_member_required, name='dispatch')
class ServersStatisticsView(UnfoldModelAdminViewMixin, TemplateView):
    template_name = 'admin/statistics/servers.html'
    title = "Статистика серверов"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(admin.site.each_context(self.request))
        context['server_stats'] = get_servers_statistics()
        return context

@method_decorator(staff_member_required, name='dispatch')
class ClientAccessLogsView(UnfoldModelAdminViewMixin, TemplateView):
    template_name = 'admin/statistics/client_logs.html'
    title = "Логи доступа клиента"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(admin.site.each_context(self.request))
        uuid = self.kwargs.get('uuid')
        
        if not uuid:
            raise Http404("UUID не указан")
        
        client_data = get_client_access_logs(uuid)
        if not client_data:
            raise Http404("Клиент не найден")
            
        context['client_data'] = client_data
        return context

@method_decorator(staff_member_required, name='dispatch')
class TimeReportsView(UnfoldModelAdminViewMixin, TemplateView):
    template_name = 'admin/statistics/time_reports.html'
    title = "Отчеты по периодам"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(admin.site.each_context(self.request))
        period = self.kwargs.get('period', 'day')
        
        if period not in ['day', 'week', 'month']:
            period = 'day'
            
        context['period'] = period
        context['period_data'] = get_time_period_data(period)
        return context 