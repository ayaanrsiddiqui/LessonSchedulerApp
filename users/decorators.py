from django.shortcuts import redirect

# Block User Administrator from basic functionalities
def block_user_admin(view_func):
    def wrapper(request, *args, **kwargs):
        if hasattr(request.user, 'profile') and request.user.profile.role == "admin_user":
            return redirect("manage_roles")
        return view_func(request, *args, **kwargs)
    return wrapper

# Allow only User Administrators
def admin_only(view_func):
    def wrapper(request, *args, **kwargs):
        if not hasattr(request.user, 'profile') or request.user.profile.role != "admin_user":
            return redirect("home")
        return view_func(request, *args, **kwargs)
    return wrapper