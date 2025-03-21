from django.contrib import admin
from .models import CustomUser
class CustomUserAdmin(admin.ModelAdmin):
    model = CustomUser
    list_display = ('email', 'firstname', 'lastname', 'is_admin')
    search_fields = ('email', 'firstname', 'lastname')
    readonly_fields = ('id',)
    ordering = ('email',)

    filter_horizontal = ()
    list_filter = ()
    fieldsets = ()


admin.site.register(CustomUser, CustomUserAdmin)