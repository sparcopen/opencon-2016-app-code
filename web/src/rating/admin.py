from django.contrib import admin
from .models import User, Step1Rating, Step2Rating


class UserAdmin(admin.ModelAdmin):
    list_display = ('nick', 'email', 'first_name', 'last_name', 'organizer', 'invitation_sent', 'disabled_at')


admin.site.register(User, UserAdmin)


class Step1RatingAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_by', 'application', 'rating')
    list_per_page = 500  # pagination
    search_fields = ('application__first_name', 'application__last_name', 'application__email', )


admin.site.register(Step1Rating, Step1RatingAdmin)


class Step2RatingAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_by', 'application', 'rating')
    list_per_page = 500  # pagination
    search_fields = ('application__first_name', 'application__last_name', 'application__email', )

admin.site.register(Step2Rating, Step2RatingAdmin)
