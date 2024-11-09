from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from django.utils.translation import gettext_lazy as _

from accounts.models import User


@admin.register(User)
class UserAdmin(DefaultUserAdmin):
    list_display = ["username", "email", "first_name", "last_name", "is_staff" , "is_active"]
    list_display_links = ['username']
    list_filter = ['gender' , 'is_staff' , 'is_superuser' , 'is_active']
    sortable_by = ['username']
    list_editable = ['is_staff' , 'is_active']
    fieldsets = (
        (_("General info"), {"fields": ("username", "password")}),
        (("Personal info") , {"fields": ("first_name" , "last_name" , "email" , "gender" , "age" , "description")}),
        (("Contact info") , {"fields": ("phone" , "address")}),
        (("Permissions") , {"fields": ("is_active" , "is_staff" , "is_superuser" ,  "groups" , "user_permissions")}),
        (("Important dates") , {"fields": ("last_login" , "date_joined")}),
    )
    

