from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class clInput(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date_created = models.DateTimeField(auto_now_add=True)
    c1 = models.BooleanField(default=0)
    c1_comment = models.TextField(default=None, null=True)
    c2 = models.BooleanField(default=0)
    c2_comment = models.TextField(default=None, null=True)
    c3 = models.BooleanField(default=0)
    c3_comment = models.TextField(default=None, null=True)
    c4 = models.BooleanField(default=0)
    c4_comment = models.TextField(default=None, null=True)
    c5 = models.BooleanField(default=0)
    c5_comment = models.TextField(default=None, null=True)
    c6 = models.BooleanField(default=0)
    c6_comment = models.TextField(default=None, null=True)

    def __str__(self):
        return str(self.date_created)
