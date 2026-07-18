from flask import Blueprint, redirect, url_for, flash, render_template
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Favorite, Listing

favorites_bp = Blueprint("favorites", __name__, url_prefix="/watchlist")


@favorites_bp.route("/")
@login_required
def index():
    favorites = (
        Favorite.query.filter_by(user_id=current_user.id)
        .order_by(Favorite.created_at.desc())
        .all()
    )
    return render_template("listings/watchlist.html", favorites=favorites)


@favorites_bp.route("/<int:listing_id>/toggle", methods=["POST"])
@login_required
def toggle(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    existing = Favorite.query.filter_by(
        user_id=current_user.id, listing_id=listing.id
    ).first()

    if existing:
        db.session.delete(existing)
        db.session.commit()
        flash("Removed from watchlist.", "info")
    else:
        db.session.add(Favorite(user_id=current_user.id, listing_id=listing.id))
        db.session.commit()
        flash("Added to watchlist.", "success")

    return redirect(url_for("listings.detail", listing_id=listing.id))
