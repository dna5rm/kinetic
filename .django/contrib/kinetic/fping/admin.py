from django.contrib import admin
from .models import agent, host

# Register your models here.
admin.site.register(agent)
admin.site.register(host)