"""
URL configuration for django_adminka project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from vpnpanel.views_statistics import StatisticsHomeView, UsersStatisticsView, ServersStatisticsView, ClientAccessLogsView, TimeReportsView
from vpnpanel.admin import financial_report_view

urlpatterns = [
    path('admin_tools/', include('admin_tools.urls')),
    path('admin/', admin.site.urls),
    
    # Маршруты статистики
    path('admin/statistics/', StatisticsHomeView.as_view(), name='statistics_home'),
    path('admin/statistics/users/', UsersStatisticsView.as_view(), name='statistics_users'),
    path('admin/statistics/servers/', ServersStatisticsView.as_view(), name='statistics_servers'),
    path('admin/statistics/client-logs/<str:uuid>/', ClientAccessLogsView.as_view(), name='statistics_client_logs'),
    path('admin/statistics/time-reports/<str:period>/', TimeReportsView.as_view(), name='statistics_time_reports'),
    path('admin/statistics/time-reports/', TimeReportsView.as_view(), name='statistics_time_reports_default'),
    path('admin/financial-report/', financial_report_view, name='financial_report'),
]
