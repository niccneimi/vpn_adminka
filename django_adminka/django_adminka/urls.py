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

admin.site.register_view('statistics/', StatisticsHomeView.as_view(), 'statistics_home')
admin.site.register_view('statistics/users/', UsersStatisticsView.as_view(), 'statistics_users')
admin.site.register_view('statistics/servers/', ServersStatisticsView.as_view(), 'statistics_servers')
admin.site.register_view('statistics/client-logs/<str:uuid>/', ClientAccessLogsView.as_view(), 'statistics_client_logs')
admin.site.register_view('statistics/time-reports/<str:period>/', TimeReportsView.as_view(), 'statistics_time_reports')
admin.site.register_view('statistics/time-reports/', TimeReportsView.as_view(), 'statistics_time_reports_default')
admin.site.register_view('financial-report/', financial_report_view, 'financial_report')

urlpatterns = [
    path('admin_tools/', include('admin_tools.urls')),
    path('admin/', admin.site.urls),
]
