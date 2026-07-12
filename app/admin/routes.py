from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app.extensions import db
from app.utils import admin_required
from app.models import User, Category, Listing, Order, Review, Favorite, Message

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/")
@login_required
@admin_required
def dashboard():
    stats = {
        "users": User.query.count(),
        "listings": Listing.query.count(),
        "available_listings": Listing.query.filter_by(status="available").count(),
        "orders": Order.query.count(),
        "reviews": Review.query.count(),
        "categories": Category.query.count(),
    }
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_listings = Listing.query.order_by(Listing.created_at.desc()).limit(5).all()
    return render_template("admin/dashboard.html", stats=stats,
                            recent_users=recent_users, recent_listings=recent_listings)


# ---------------- Users ----------------

@admin_bp.route("/users")
@login_required
@admin_required
def users():
    all_users = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin/users.html", users=all_users)


@admin_bp.route("/users/<int:user_id>/toggle-admin", methods=["POST"])
@login_required
@admin_required
def toggle_admin(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You can't change your own admin status.", "warning")
        return redirect(url_for("admin.users"))

    user.is_admin = not user.is_admin
    db.session.commit()
    flash(f"{user.full_name} is now {'an admin' if user.is_admin else 'a regular user'}.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/toggle-ban", methods=["POST"])
@login_required
@admin_required
def toggle_ban(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You can't ban your own account.", "warning")
        return redirect(url_for("admin.users"))

    user.is_banned = not user.is_banned
    db.session.commit()
    flash(f"{user.full_name} has been {'banned' if user.is_banned else 'unbanned'}.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You can't delete your own account.", "warning")
        return redirect(url_for("admin.users"))

    # Explicit cleanup of dependent rows (safe regardless of DB cascade config)
    for listing in Listing.query.filter_by(seller_id=user.id).all():
        db.session.delete(listing)  # cascades to that listing's orders/reviews/favorites/messages
    Order.query.filter_by(buyer_id=user.id).delete()
    Review.query.filter_by(reviewer_id=user.id).delete()
    Favorite.query.filter_by(user_id=user.id).delete()
    Message.query.filter_by(sender_id=user.id).delete()

    db.session.delete(user)
    db.session.commit()
    flash(f"Account for {user.full_name} and all associated data has been deleted.", "info")
    return redirect(url_for("admin.users"))


# ---------------- Categories ----------------

@admin_bp.route("/categories", methods=["GET", "POST"])
@login_required
@admin_required
def categories():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Category name cannot be empty.", "danger")
        elif Category.query.filter_by(name=name).first():
            flash("That category already exists.", "danger")
        else:
            db.session.add(Category(name=name))
            db.session.commit()
            flash(f"Category '{name}' created.", "success")
        return redirect(url_for("admin.categories"))

    all_categories = Category.query.order_by(Category.name).all()
    return render_template("admin/categories.html", categories=all_categories)


@admin_bp.route("/categories/<int:category_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_category(category_id):
    category = Category.query.get_or_404(category_id)
    if category.listings:
        flash(f"Can't delete '{category.name}' — {len(category.listings)} listing(s) still use it.", "danger")
    else:
        db.session.delete(category)
        db.session.commit()
        flash("Category deleted.", "info")
    return redirect(url_for("admin.categories"))


# ---------------- Listings (moderation) ----------------

@admin_bp.route("/listings")
@login_required
@admin_required
def listings():
    all_listings = Listing.query.order_by(Listing.created_at.desc()).all()
    return render_template("admin/listings.html", listings=all_listings)


@admin_bp.route("/listings/<int:listing_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_listing(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    title = listing.title
    db.session.delete(listing)
    db.session.commit()
    flash(f"Listing '{title}' removed by admin.", "info")
    return redirect(url_for("admin.listings"))


# ---------------- Orders (read-only oversight) ----------------

@admin_bp.route("/orders")
@login_required
@admin_required
def orders():
    all_orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template("admin/orders.html", orders=all_orders)


# ---------------- Reviews (moderation) ----------------

@admin_bp.route("/reviews")
@login_required
@admin_required
def reviews():
    all_reviews = Review.query.order_by(Review.created_at.desc()).all()
    return render_template("admin/reviews.html", reviews=all_reviews)


@admin_bp.route("/reviews/<int:review_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_review(review_id):
    review = Review.query.get_or_404(review_id)
    db.session.delete(review)
    db.session.commit()
    flash("Review removed by admin.", "info")
    return redirect(url_for("admin.reviews"))
