from flask import Blueprint, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Review, Listing

reviews_bp = Blueprint("reviews", __name__, url_prefix="/reviews")


@reviews_bp.route("/listing/<int:listing_id>/add", methods=["POST"])
@login_required
def add(listing_id):
    listing = Listing.query.get_or_404(listing_id)

    if listing.seller_id == current_user.id:
        flash("You can't review your own listing.", "warning")
        return redirect(url_for("listings.detail", listing_id=listing.id))

    rating = request.form.get("rating", type=int)
    comment = request.form.get("comment", "").strip()

    if rating is None or not (1 <= rating <= 5):
        flash("Rating must be between 1 and 5.", "danger")
        return redirect(url_for("listings.detail", listing_id=listing.id))
    if not comment:
        flash("Please write a short comment with your review.", "danger")
        return redirect(url_for("listings.detail", listing_id=listing.id))

    review = Review(
        listing_id=listing.id,
        reviewer_id=current_user.id,
        rating=rating,
        comment=comment[:500],
    )
    db.session.add(review)
    db.session.commit()
    flash("Review submitted.", "success")
    return redirect(url_for("listings.detail", listing_id=listing.id))


@reviews_bp.route("/<int:review_id>/delete", methods=["POST"])
@login_required
def delete(review_id):
    review = Review.query.get_or_404(review_id)
    if review.reviewer_id != current_user.id:
        abort(403)  # only the author may delete their own review

    listing_id = review.listing_id
    db.session.delete(review)
    db.session.commit()
    flash("Review deleted.", "info")
    return redirect(url_for("listings.detail", listing_id=listing_id))
                                                                             
