from django.db import models
import uuid
class Department(models.Model):
    name = models.CharField(max_length=100 , blank=False , null=False)
    description = models.TextField()

class Basic_Info(models.Model):
    product_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product_name = models.CharField(max_length=100 , blank=False , null=False)
    sku = models.CharField(max_length=100 , blank=False , null=False)
    department_id = models.ForeignKey(Department, on_delete=models.CASCADE)
    qty = models.IntegerField()

class PriceCost(models.Model):
    basic_info_id = models.ForeignKey(Basic_Info, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=20 , decimal_places=2 , blank=False , null=False)
    cost = models.DecimalField(max_digits=20 , decimal_places=2 , blank=False , null = False)