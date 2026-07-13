import os
from flask import Flask, session
from config import Config
from app.extensions import db, login_manager, csrf


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure upload folder exists
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # --- Init extensions ---
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    # --- Register blueprints ---
    from app.auth.routes import auth_bp
    from app.main.routes import main_bp
    from app.listings.routes import listings_bp
    from app.orders.routes import orders_bp
    from app.reviews.routes import reviews_bp
    from app.favorites.routes import favorites_bp
    from app.admin.routes import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(listings_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(reviews_bp)
    app.register_blueprint(favorites_bp)
    app.register_blueprint(admin_bp)

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # --- Security headers on every response ---
    @app.after_request
    def set_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "same-origin"
        # Basic CSP: adjust if you add more external script sources
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "style-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; "
            "script-src 'self' https://cdn.jsdelivr.net; "
            "img-src 'self' data:;"
        )
        return response

    # --- Refresh session expiry on every request the user is active ---
    @app.before_request
    def make_session_permanent():
        session.permanent = True

    # --- Kick out a user immediately if they get banned mid-session ---
    @app.before_request
    def enforce_ban():
        from flask_login import current_user, logout_user
        if current_user.is_authenticated and current_user.is_banned:
            logout_user()
            session.clear()

    # --- Error handlers ---
    @app.errorhandler(404)
    def not_found(e):
        from flask import render_template
        return render_template("errors/404.html"), 404

    @app.errorhandler(403)
    def forbidden(e):
        from flask import render_template
        return render_template("errors/403.html"), 403

    # --- CLI helper: flask seed-db ---
    @app.cli.command("seed-db")
    def seed_db():
        """Create tables and seed default categories."""
        from app.models import Category
        db.create_all()
        defaults = ["Textbooks", "Electronics", "Lab Equipment", "Stationery", "Other"]
        for name in defaults:
            if not Category.query.filter_by(name=name).first():
                db.session.add(Category(name=name))
        db.session.commit()
        print("Database seeded.")

    # --- CLI helper: flask make-admin <email> ---
    import click

    @app.cli.command("make-admin")
    @click.argument("email")
    def make_admin(email):
        """Promote an existing user (by email) to admin. Usage: flask --app run make-admin someone@example.com"""
        from app.models import User
        user = User.query.filter_by(email=email.strip().lower()).first()
        if not user:
            print(f"No user found with email {email}.")
            return
        user.is_admin = True
        db.session.commit()
        print(f"{user.full_name} ({user.email}) is now an admin.")

    return app
