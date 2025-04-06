from django.contrib import admin
from .models import CustomUser, Project

class CustomUserAdmin(admin.ModelAdmin):
    model = CustomUser
    list_display = ('email', 'firstname', 'lastname', 'is_admin')
    search_fields = ('email', 'firstname', 'lastname')
    readonly_fields = ('id',)
    ordering = ('email',)

    filter_horizontal = ()
    list_filter = ()
    fieldsets = ()

class ProjectAdmin(admin.ModelAdmin):
    model = Project
    list_display = ('project_name', 'description', 'project_type', 'status', 'created_at')
    search_fields = ('project_name', 'description', 'project_type', 'status')
    readonly_fields = ('id', 'created_at')
    ordering = ('created_at',)

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Project, ProjectAdmin)
