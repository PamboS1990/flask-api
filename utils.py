from flask_smorest import abort


def check_admin_access(jwt):
    if not jwt.get("is_admin"):
        abort(401, message="Admin privilege required.")
