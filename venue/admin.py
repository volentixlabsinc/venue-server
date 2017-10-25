from venue.models import ForumSite, Signature, UserProfile, ForumProfile, UptimeBatch, SignatureCheck, PointsCalculation, GlobalStats
from django.utils.translation import ugettext_lazy
from django.contrib.auth.models import User
from django.contrib import admin

class MyAdminSite(admin.AdminSite):
    # Text to put at the end of each page's <title>.
    site_title = ugettext_lazy('Volentix administration')
    # Text to put in each page's <h1> (and above login form).
    site_header = ugettext_lazy('Volentix administration')
    # Text to put at the top of the admin index page.
    index_title = ugettext_lazy('Apps and Data')

admin_site = MyAdminSite()

admin_site.register(User)
admin_site.register(ForumSite)
admin_site.register(Signature)
admin_site.register(UptimeBatch)
admin_site.register(PointsCalculation)
admin_site.register(GlobalStats)

class SignatureCheckAdmin(admin.ModelAdmin):
    list_display = ['forum_site', 'forum_user_id', 
        'uptime_batch', 'total_posts', 'signature_found']
        
    def forum_site(self, obj):
        return obj.uptime_batch.forum_profile.forum
        
    def forum_user_id(self, obj):
        return obj.uptime_batch.forum_profile.user_profile
    
admin_site.register(SignatureCheck, SignatureCheckAdmin)

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'total_points', 'total_tokens']
    
    def total_points(self, obj):
        return obj.get_total_points()
        
    def total_tokens(self, obj):
        return obj.get_total_tokens()
        
admin_site.register(UserProfile, UserProfileAdmin)

class ForumProfileAdmin(admin.ModelAdmin):
    list_display = ['forum_user_id', 'forum']
    
admin_site.register(ForumProfile, ForumProfileAdmin)