from admin_tools.menu import items, Menu

class CustomMenu(Menu):
    def __init__(self, **kwargs):
        Menu.__init__(self, **kwargs)
        self.children += [
            items.MenuItem('Dashboard', '/admin/'),
            items.AppList('VPNPANEL', models=('vpnpanel.*',)),
            items.MenuItem('Добавить сервер', '/admin/vpnpanel/server/add-server/'),
            items.MenuItem('Для фин. отчёта', '/admin/financial-report/'),
            items.MenuItem('Рассылка в боте', '/admin/bot-sending/')
        ]