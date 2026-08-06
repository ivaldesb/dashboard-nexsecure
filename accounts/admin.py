from django.contrib import admin

from accounts.models import Role, User

admin.site.register(User)
admin.site.register(Role)
