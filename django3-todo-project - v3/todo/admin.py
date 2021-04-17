from django.contrib import admin
from .models import Profile, Todo

admin.site.register(Profile)


class TodoAdmin(admin.ModelAdmin):
    readonly_fields = ('created',)

admin.site.register(Todo, TodoAdmin)
