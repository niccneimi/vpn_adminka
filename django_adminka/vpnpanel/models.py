from django.db import models

class User(models.Model):
    user_id = models.BigIntegerField(primary_key=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    lang = models.CharField(max_length=100, default='Русский')
    free_trial_used = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def client_keys(self):
        return ClientAsKey.objects.filter(telegram_id=str(self.user_id))

    class Meta:
        db_table = 'users'
        managed = False

class CryptoAddress(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, db_column='user_id')
    address = models.CharField(max_length=255)
    token = models.CharField(max_length=10)
    standart = models.CharField(max_length=10, default='BEP20')
    result = models.CharField(max_length=20, default='pending')
    address_type = models.CharField(max_length=20, default='default')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'crypto_addresses'
        managed = False

class CryptoTransaction(models.Model):
    id = models.AutoField(primary_key=True)
    txid = models.CharField(max_length=255)
    transaction_type = models.CharField(max_length=12, default='IN')
    confirmations = models.IntegerField(default=0)
    token = models.CharField(max_length=10)
    amount = models.DecimalField(max_digits=20, decimal_places=8)
    from_address = models.CharField(max_length=42)
    standart = models.CharField(max_length=10, default='BEP20')
    user_crypto_address_id = models.ForeignKey(CryptoAddress, on_delete=models.DO_NOTHING, db_column='user_crypto_address_id', null=True)
    address = models.CharField(max_length=42)
    paid = models.BooleanField(default=False)
    status = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'crypto_transactions'
        managed = False
        unique_together = (('txid', 'address'),)

class Order(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, db_column='user_id')
    amount = models.DecimalField(max_digits=20, decimal_places=8)
    currency = models.CharField(max_length=10)
    paid = models.BooleanField(default=False)
    extra = models.JSONField(blank=True, null=True)
    package_size = models.IntegerField()
    promocode_used = models.BooleanField()
    expiration_date = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'orders'
        managed = False

class ClientAsKey(models.Model):
    id = models.AutoField(primary_key=True)
    telegram_id = models.CharField(max_length=255)
    host = models.CharField(max_length=255, blank=True, null=True)
    uuid = models.CharField(max_length=255, blank=True, null=True)
    email = models.CharField(max_length=255, blank=True, null=True)
    public_key = models.CharField(max_length=255, blank=True, null=True)
    online_count = models.IntegerField(default=0)
    online_ips = models.CharField(max_length=255, blank=True, null=True)
    expiration_date = models.IntegerField(blank=True, null=True)
    deleted = models.IntegerField(default=0)
    notified_2_days = models.BooleanField(default=False)
    notified_1_day = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'clients_as_keys'
        managed = False

class UsedPromocode(models.Model):
    id = models.AutoField(primary_key=True)
    user_id = models.CharField(max_length=255)
    promocode = models.CharField(max_length=255)

    class Meta:
        db_table = 'used_promocodes'
        managed = False

class Server(models.Model):
    id = models.AutoField(primary_key=True)
    host = models.CharField(max_length=255, unique=True)
    port = models.IntegerField(default=22)
    username = models.CharField(max_length=255, blank=True, null=True)
    password = models.CharField(max_length=255, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    public_key = models.CharField(max_length=255, blank=True, null=True)
    private_key = models.CharField(max_length=255, blank=True, null=True)
    clients_on_server = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    created = models.IntegerField(default=0)

    class Meta:
        db_table = 'servers'
        managed = False

class Tarif(models.Model):
    id = models.AutoField(primary_key=True)
    price = models.IntegerField(null=False)
    days = models.IntegerField(null=False)

    class Meta:
        db_table = 'tarifs'
        managed = False
