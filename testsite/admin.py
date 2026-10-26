from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Photographer, User

# Register your models here.
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active')
    fieldsets = UserAdmin.fieldsets + (('Loma', {'fields': ('role',)}),)
    add_fieldsets = UserAdmin.add_fieldsets + (('Loma', {'fields': ('email', 'role')}),)


@admin.register(Photographer)
class PhotographerAdmin(admin.ModelAdmin):
    list_display = ('user', 'description')
