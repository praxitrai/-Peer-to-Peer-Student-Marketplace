from functools import wraps
from flask import abort
from flask_login import current_user


def admin_required(view_func):
    """Restrict a route to authenticated users with is_admin=True.

    Distinct from @login_required: this checks *authorization* (what the
    user is allowed to do), not just *authentication* (who they are).
    Unauthenticated users get redirected to login by Flask-Login as usual;
    authenticated non-admins get a 403.
    """
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(401)
        if not current_user.is_admin:
            abort(403)
        return view_func(*args, **kwargs)
    return wrapped
                             
