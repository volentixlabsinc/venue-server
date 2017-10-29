from django.apps import AppConfig


class VenueConfig(AppConfig):
    name = 'venue'
    
    def ready(self):
        from django.contrib import admin
        from django.contrib.admin import sites
        
        class MyAdminSite(admin.AdminSite):
            # Text to put at the end of each page's <title>.
            site_title = 'Volentix administration'
            # Text to put in each page's <h1> (and above login form).
            site_header = 'Volentix administration'
            # Text to put at the top of the admin index page.
            index_title = 'Apps and Data'
            
        admin_site = MyAdminSite()
        admin.site = admin_site
        sites.site = admin_site