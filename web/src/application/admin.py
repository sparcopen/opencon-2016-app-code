from django.contrib import admin
from .models import Institution, Organization, Application, Country, Draft, Reference
from .forms import ApplicationForm, ChangeStatusAdminForm


class DraftAdmin(admin.ModelAdmin):
    list_display = ('email', 'uuid', 'created_at', 'updated_at', 'inactive')
    fields = ('email', 'uuid', 'created_at', 'updated_at', 'data', 'inactive')
    readonly_fields = ('email', 'uuid', 'created_at', 'updated_at', 'inactive')
    list_per_page = 500 # pagination
    search_fields = ('email', 'uuid')

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

admin.site.register(Draft, DraftAdmin)


class InstitutionAdmin(admin.ModelAdmin):
    pass

admin.site.register(Institution, InstitutionAdmin)


class OrganizationAdmin(admin.ModelAdmin):
    pass

admin.site.register(Organization, OrganizationAdmin)


class CountryAdmin(admin.ModelAdmin):
    readonly_fields = ('name', )

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False


admin.site.register(Country, CountryAdmin)


class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'status', 'created_at', 'get_rating1',
                    'need_rating1', 'get_rating2', 'need_rating2')
    readonly_fields = ('created_at', 'get_data', 'status', 'status_at', 'status_by', 'status_ip')
    form = ApplicationForm
    search_fields = ('first_name', 'last_name', 'email', )

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

admin.site.register(Application, ApplicationAdmin)


class ChangeStatus(Application):
    class Meta:
        proxy = True


class ChangeStatusAdmin(admin.ModelAdmin):
    list_editable = ('status', )
    list_display = ('full_name', 'email', 'status')
    readonly_fields = ('status_by', 'status_ip', 'status_at')
    list_per_page = 500 # pagination
    search_fields = ('first_name', 'last_name', 'email', )
    form = ChangeStatusAdminForm

    def get_changelist_form(self, request, **kwargs):
        kwargs.setdefault('form', ChangeStatusAdminForm)
        return super().get_changelist_form(request, **kwargs)

    def get_queryset(self, request):
        return Application.objects.get_all()

    def response_change(self, request, obj):
        ip = request.META.get('HTTP_X_REAL_IP') or request.META['REMOTE_ADDR']
        obj.change_status(obj.status, None, ip, obj.status_reason)
        return super().response_change(request, obj)

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

admin.site.register(ChangeStatus, ChangeStatusAdmin)


class ReferenceAdmin(admin.ModelAdmin):
    list_display = ('key', 'name')

admin.site.register(Reference, ReferenceAdmin)
