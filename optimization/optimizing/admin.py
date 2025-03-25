from django.contrib import admin
from .models import LinkedInProfile, ProfileStatus, Candidate, LinkedInMessage
# Register your models here.

admin.site.register(LinkedInProfile)
admin.site.register(ProfileStatus)
admin.site.register(Candidate)


class LinkedInMessageAdmin(admin.ModelAdmin):
    list_display=['classified_status','profile', 'created_at']
    search_fields = ['classified_status']
    @admin.display(description='profile')
    def profile(self, object):
        return object.profile.profile_id
    
admin.site.register(LinkedInMessage, LinkedInMessageAdmin)