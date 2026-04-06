from django.shortcuts import redirect
from django.urls import resolve

# Block User Administrator from basic functionalities
def block_user_admin(view_func):
    def wrapper(request, *args, **kwargs):
        if hasattr(request.user, 'profile') and request.user.profile.role == "admin_user":
            # Allow access to login, logout, and home pages
            try:
                current_url_name = resolve(request.path_info).url_name
                allowed_urls = ['login', 'logout', 'home']
                if current_url_name in allowed_urls:
                    return view_func(request, *args, **kwargs)
            except:
                pass
            return redirect("manage_roles")
        return view_func(request, *args, **kwargs)
    return wrapper

# Allow only User Administrators
def admin_only(view_func):
    def wrapper(request, *args, **kwargs):
        if not hasattr(request.user, 'profile') or request.user.profile.role != "admin_user":
            return redirect("index")
        return view_func(request, *args, **kwargs)
    return wrapper