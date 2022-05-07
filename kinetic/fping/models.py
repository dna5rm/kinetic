from django.db import models
from django.core.validators import RegexValidator
from django.utils.timezone import now

# Create your models here.
class agent(models.Model):
    agent = models.CharField(max_length=15, primary_key=True, validators=[RegexValidator('^[A-Z_]*$', 'Only uppercase letters and underscores allowed.')])
    active = models.BooleanField(default=1)
    
    def __str__(self):
        return self.agent

class host(models.Model):
    address = models.CharField(primary_key=True, max_length=100, unique=True)
    agent = models.ManyToManyField(agent, blank=True)
    hostname = models.CharField(max_length=150)
    enabled = models.BooleanField(default=1)

    def __str__(self):
        return self.address

class stat(models.Model):
    id = models.AutoField(primary_key=True)
    agent = models.ForeignKey(agent, on_delete=models.CASCADE)
    address = models.ForeignKey(host, on_delete=models.CASCADE)
    sample = models.IntegerField(null=False, blank=False, default=0)
    pings = models.IntegerField(null=False, blank=False, default=0)
    loss = models.IntegerField(null=False, blank=False, default=0)
    median = models.FloatField(null=False, blank=False, default=0)
    min = models.FloatField(null=False, blank=False, default=0)
    max = models.FloatField(null=False, blank=False, default=0)
    stdev = models.FloatField(null=False, blank=False, default=0)
    avg_loss = models.IntegerField(null=False, blank=False, default=0)
    avg_median = models.FloatField(null=False, blank=False, default=0)
    avg_min = models.FloatField(null=False, blank=False, default=0)
    avg_max = models.FloatField(null=False, blank=False, default=0)
    avg_stdev = models.FloatField(null=False, blank=False, default=0)    
    prev_loss = models.IntegerField(null=False, blank=False, default=0)
    last_change = models.DateTimeField(default=now)
    last_updated = models.DateTimeField(default=now)
