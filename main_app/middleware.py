from django.utils.deprecation import MiddlewareMixin
from django.urls import reverse
from django.shortcuts import redirect

class LoginCheckMiddleWare(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        modulename = view_func.__module__
        user = request.user  # Who is the current user?

        # List of paths that should be accessible without login
        public_paths = [
            reverse('login_page'),
            reverse('user_login'),
            '/widget',
            '/chatbot',
        ]

        # Public endpoints with dynamic company_id (can't use reverse easily)
        if request.path.startswith("/ID/") and (
            request.path.endswith("/chat") or request.path.endswith("/feedback")
        ):
            return None  # Allow public access

        if user.is_authenticated:
            if user.user_type == '1':  # Admin/HOD
                if modulename == 'main_app.student_views':
                    return redirect(reverse('admin_home'))
            elif user.user_type == '2':  # Staff
                if modulename in ['main_app.student_views', 'main_app.hod_views']:
                    return redirect(reverse('staff_home'))
            elif user.user_type == '3':  # Student
                if modulename in ['main_app.hod_views', 'main_app.staff_views']:
                    return redirect(reverse('student_home'))
            else:  # Unknown type, send to login
                return redirect(reverse('login_page'))
        else:
            # Allow login-related & public endpoints
            if request.path in public_paths or modulename == 'django.contrib.auth.views':
                return None
            else:
                return redirect(reverse('login_page'))
