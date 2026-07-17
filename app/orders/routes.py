from flask import Blueprint, redirect, url_for, flash, render_template, abort, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Order, Listing

orders_bp = Blueprint("orders", __name__, url_prefix="/orders")

VALID_TRANSITIONS = {
    "pending": {"confirmed", "cancelled"},
    "confirmed": {"completed", "cancelled"},
    "completed": set(),
    "cancelled": set(),
}


@orders_bp.route("/place/<int:listing_id>", methods=["POST"])
@login_required
def place(listing_id):
    listing = Listing.query.get_or_404(listing_id)

    if listing.seller_id == current_user.id:
        flash("You can't order your own listing.", "warning")
        return redirect(url_for("listings.detail", listing_id=listing.id))
    if listing.status != "available":
        flash("This item is no longer available.", "warning")
        return redirect(url_for("listings.detail", listing_id=listing.id))

    order = Order(listing_id=listing.id, buyer_id=current_user.id, status="pending")
    db.session.add(order)
    db.session.commit()
    flash("Order placed. The seller will confirm it shortly.", "success")
    return redirect(url_for("orders.my_orders"))


@orders_bp.route("/mine")
@login_required
def my_orders():
    orders = (
        Order.query.filter_by(buyer_id=current_user.id)
        .order_by(Order.created_at.desc())
        .all()
    )
    return render_template("orders/my_orders.html", orders=orders)


@orders_bp.route("/selling")
@login_required
def selling_orders():
    orders = (
        Order.query.join(Listing, Order.listing_id == Listing.id)
        .filter(Listing.seller_id == current_user.id)
        .order_by(Order.created_at.desc())
        .all()
    )
    return render_template("orders/selling_orders.html", orders=orders)


@orders_bp.route("/<int:order_id>/status", methods=["POST"])
@login_required
def update_status(order_id):
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get("status")

    is_seller = order.listing.seller_id == current_user.id
    is_buyer = order.buyer_id == current_user.id
    if not (is_seller or is_buyer):
        abort(403)

    # Buyers may only cancel their own pending order; sellers control the rest
    if is_buyer and not is_seller:
        if new_status != "cancelled" or order.status != "pending":
            abort(403)

    if new_status not in VALID_TRANSITIONS.get(order.status, set()):
        flash("Invalid status change.", "danger")
    else:
        order.status = new_status
        if new_status == "completed":
            order.listing.status = "sold"
        db.session.commit()
        flash(f"Order marked as {new_status}.", "success")

    return redirect(request.referrer or url_for("orders.my_orders"))
