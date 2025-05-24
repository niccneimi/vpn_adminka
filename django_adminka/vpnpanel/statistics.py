from django.db import connection
from .models import User, ClientAsKey, Server, Order
from django.db.models import Count, F, Sum, Case, When, IntegerField, Value, Q
from django.utils import timezone
import datetime
import requests
from django.conf import settings
import json
from collections import defaultdict

def get_users_statistics():
    """Получает общую статистику по пользователям."""
    total_users = User.objects.count()
    now_timestamp = int(datetime.datetime.now().timestamp())
    active_users_ids = ClientAsKey.objects.filter(
        expiration_date__gt=now_timestamp, 
        deleted=0
    ).values_list('telegram_id', flat=True).distinct()
    
    active_users_count = len(active_users_ids)
    inactive_users_count = total_users - active_users_count
    
    return {
        'total_users': total_users,
        'active_users': active_users_count,
        'inactive_users': inactive_users_count,
        'active_percentage': round((active_users_count / total_users * 100) if total_users > 0 else 0, 2)
    }

def get_servers_statistics():
    """Получает статистику по серверам."""
    servers = Server.objects.filter(created=1)
    
    server_stats = []
    for server in servers:
        active_clients_count = ClientAsKey.objects.filter(
            host=server.host,
            deleted=0,
            expiration_date__gt=int(datetime.datetime.now().timestamp())
        ).count()
        
        active_sessions = ClientAsKey.objects.filter(
            host=server.host,
            deleted=0,
            expiration_date__gt=int(datetime.datetime.now().timestamp())
        ).aggregate(total_online=Sum('online_count'))['total_online'] or 0
        
        server_stats.append({
            'id': server.id,
            'host': server.host,
            'location': server.location,
            'clients_total': server.clients_on_server,
            'active_clients': active_clients_count,
            'active_sessions': active_sessions
        })
    
    return server_stats

def get_client_access_logs(uuid):
    """Получает логи доступа для конкретного UUID."""
    client = ClientAsKey.objects.filter(uuid=uuid, deleted=0).first()
    
    if not client:
        return None
    
    logs = []
    
    if client.online_ips:
        ips = client.online_ips.split(':')
        for ip in ips:
            if ip:
                try:
                    response = requests.get(f"https://ipinfo.io/{ip}/json")
                    if response.status_code == 200:
                        ip_data = response.json()
                        country = ip_data.get('country', 'Unknown')
                        city = ip_data.get('city', 'Unknown')
                    else:
                        country = "Unknown"
                        city = "Unknown"
                except Exception:
                    country = "Unknown"
                    city = "Unknown"
                
                logs.append({
                    'ip': ip,
                    'country': country,
                    'city': city,
                    'online': True,
                    'last_seen': datetime.datetime.now()
                })
    
    return {
        'telegram_id': client.telegram_id,
        'uuid': client.uuid,
        'host': client.host,
        'logs': logs
    }

def get_time_period_data(period='day', start_date=None, end_date=None):
    """Получает статистику по указанному периоду."""
    today = timezone.now().date()
    
    if period == 'all_time':
        start_datetime = datetime.datetime(2000, 1, 1)
        end_datetime = datetime.datetime.combine(today, datetime.time.max)
    elif start_date and end_date:
        start_datetime = datetime.datetime.combine(start_date, datetime.time.min)
        end_datetime = datetime.datetime.combine(end_date, datetime.time.max)
    else:
        if period == 'day':
            start_date = today
        elif period == 'week':
            start_date = today - datetime.timedelta(days=7)
        elif period == 'month':
            start_date = today.replace(day=1)
        else:
            raise ValueError(f"Неподдерживаемый период: {period}")

        start_datetime = datetime.datetime.combine(start_date, datetime.time.min)
        end_datetime = datetime.datetime.combine(today, datetime.time.max)
    
    new_users = User.objects.filter(
        created_at__gte=start_datetime,
        created_at__lte=end_datetime
    ).count()
    
    new_orders = Order.objects.filter(
        created_at__gte=start_datetime,
        created_at__lte=end_datetime
    ).count()
    
    orders_sum = Order.objects.filter(
        created_at__gte=start_datetime,
        created_at__lte=end_datetime
    ).aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    new_keys = ClientAsKey.objects.filter(
        created_at__gte=start_datetime,
        created_at__lte=end_datetime
    ).count()
    
    return {
        'period': period,
        'start_date': start_date if period != 'all_time' else None,
        'end_date': end_date or today if period != 'all_time' else None,
        'new_users': new_users,
        'new_orders': new_orders,
        'orders_sum': round(float(orders_sum), 2),
        'new_keys': new_keys
    } 