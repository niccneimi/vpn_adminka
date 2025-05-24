from django.views.generic import TemplateView
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import ClientAsKey
from django.shortcuts import get_object_or_404
from django.http import Http404
from django.contrib import admin
from .statistics import (
    get_users_statistics, get_servers_statistics, 
    get_client_access_logs, get_time_period_data
)
import datetime

class UnfoldStyleViewMixin(LoginRequiredMixin):
    """Миксин для имитации стиля Unfold без зависимости от UnfoldModelAdminViewMixin."""
    title = None
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Добавляем стандартный контекст админки
        context.update(admin.site.each_context(self.request))
        
        # Добавляем основные переменные админ-контекста
        context['has_permission'] = True
        context['is_popup'] = False
        context['is_nav_sidebar_enabled'] = True
        context['available_apps'] = admin.site.get_app_list(self.request)
        
        # Добавляем заголовок в стиле Unfold
        if self.title:
            context['title'] = self.title
            context['subtitle'] = ''
            context['opts'] = {'app_label': 'statistics'}
            context['preserved_filters'] = ''
            context['original'] = None
            context['is_edit'] = False
            context['is_popup'] = False
            context['add'] = False
            context['change'] = False
            context['view'] = True
            
        return context

@method_decorator(staff_member_required, name='dispatch')
class StatisticsHomeView(UnfoldStyleViewMixin, TemplateView):
    template_name = 'admin/statistics/home.html'
    title = "Общая статистика"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        start_date_str = self.request.GET.get('start_date')
        end_date_str = self.request.GET.get('end_date')
        start_date = None
        end_date = None
        
        if start_date_str:
            try:
                start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass
                
        if end_date_str:
            try:
                end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        custom_period = None
        if start_date and end_date:
            custom_period = get_time_period_data('custom', start_date, end_date)
        
        context['user_stats'] = get_users_statistics()
        context['server_stats'] = get_servers_statistics()
        context['day_stats'] = get_time_period_data('day')
        context['week_stats'] = get_time_period_data('week')
        context['month_stats'] = get_time_period_data('month')
        context['custom_period'] = custom_period
        context['start_date'] = start_date_str
        context['end_date'] = end_date_str
        
        return context

@method_decorator(staff_member_required, name='dispatch')
class UsersStatisticsView(UnfoldStyleViewMixin, TemplateView):
    template_name = 'admin/statistics/users.html'
    title = "Статистика пользователей"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_stats'] = get_users_statistics()
        return context

@method_decorator(staff_member_required, name='dispatch')
class ServersStatisticsView(UnfoldStyleViewMixin, TemplateView):
    template_name = 'admin/statistics/servers.html'
    title = "Статистика серверов"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['server_stats'] = get_servers_statistics()
        return context

@method_decorator(staff_member_required, name='dispatch')
class ClientAccessLogsView(UnfoldStyleViewMixin, TemplateView):
    template_name = 'admin/statistics/client_logs.html'
    title = "Логи доступа клиента"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        uuid = self.kwargs.get('uuid')
        
        if not uuid:
            raise Http404("UUID не указан")
        
        client_data = get_client_access_logs(uuid)
        if not client_data:
            raise Http404("Клиент не найден")
            
        context['client_data'] = client_data
        return context

@method_decorator(staff_member_required, name='dispatch')
class TimeReportsView(UnfoldStyleViewMixin, TemplateView):
    template_name = 'admin/statistics/time_reports.html'
    title = "Отчеты по периодам"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        period = self.kwargs.get('period', 'day')
        
        start_date_str = self.request.GET.get('start_date')
        end_date_str = self.request.GET.get('end_date')
        
        start_date = None
        end_date = None
        
        if start_date_str:
            try:
                start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass
                
        if end_date_str:
            try:
                end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        if period == 'custom' and start_date and end_date:
            context['period'] = 'custom'
            context['period_data'] = get_time_period_data('custom', start_date, end_date)
            context['start_date'] = start_date_str
            context['end_date'] = end_date_str
        else:
            if period not in ['day', 'week', 'month']:
                period = 'day'
                
            context['period'] = period
            context['period_data'] = get_time_period_data(period)
            
        return context 