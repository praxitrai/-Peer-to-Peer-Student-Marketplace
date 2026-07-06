import os
import uuid
from flask import (Blueprint, render_template, redirect, url_for, flash,
                    request, session, abort, current_app)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.extensions import db
from app.models import Listing, Category, Message

listings_bp = Blueprint("listings", __name__, url_prefix="/listings")


def allowed_file(filename):
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in current_app.config["ALLOWED_EXTENSIONS"]


def save_upload(file_storage):
    """Validate and save an uploaded image, return the stored filename or None."""
    if not file_storage or file_storage.filename == "":
        return None
    if not allowed_file(file_storage.filename):
        flash("Unsupported image type. Use PNG, JPG, JPEG, GIF or WEBP.", "danger")
        return None

    original = secure_filename(file_storage.filename)
    ext = original.rsplit(".", 1)[-1].lower()
    # Random filename avoids collisions and avoids leaking the original path
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    dest = os.path.join(current_app.config["UPLOAD_FOLDER"], unique_name)
    file_storage.save(dest)
    return unique_name

@listings_bp.route("/")
def index():
    query = Listing.query.filter_by(status="available")

    category_id = request.args.get("category", type=int)
    min_price = request.args.get("min_price", type=float)
    max_price = request.args.get("max_price", type=float)
    search = request.args.get("q", "").strip()

    if category_id:
        query = query.filter(Listing.category_id == category_id)
    if min_price is not None:
        query = query.filter(Listing.price >= min_price)
    if max_price is not None:
        query = query.filter(Listing.price <= max_price)
    if search:
        like = f"%{search}%"
        query = query.filter(Listing.title.ilike(like))

    page = request.args.get("page", 1, type=int)
    pagination = query.order_by(Listing.created_at.desc()).paginate(
        page=page, per_page=current_app.config["ITEMS_PER_PAGE"], error_out=False
    )

    categories = Category.query.order_by(Category.name).all()

    return render_template(
        "listings/list.html",
        listings=pagination.items,
        pagination=pagination,
        categories=categories,
        selected_category=category_id,
        min_price=min_price,
        max_price=max_price,
        search=search,
    )
@listings_bp.route("/<int:listing_id>")
def detail(listing_id):
    listing = Listing.query.get_or_404(listing_id)

    # --- Recently Viewed: tracked entirely in the session ---
    recent = session.get("recently_viewed", [])
    recent = [lid for lid in recent if lid != listing.id]
    recent.insert(0, listing.id)
    session["recently_viewed"] = recent[: current_app.config["RECENTLY_VIEWED_MAX"]]

    is_favorited = False
    if current_user.is_authenticated:
        from app.models import Favorite
        is_favorited = Favorite.query.filter_by(
            user_id=current_user.id, listing_id=listing.id
        ).first() is not None

    return render_template("listings/detail.html", listing=listing, is_favorited=is_favorited)


@listings_bp.route("/new", methods=["GET", "POST"])
@login_required
def create():
    categories = Category.query.order_by(Category.name).all()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        price = request.form.get("price", type=float)
        category_id = request.form.get("category_id", type=int)
        image = request.files.get("image")

        errors = []
        if not title:
            errors.append("Title is required.")
        if not description:
            errors.append("Description is required.")
        if price is None or price <= 0:
            errors.append("Enter a valid price greater than 0.")
        if not Category.query.get(category_id or 0):
            errors.append("Please select a valid category.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("listings/create.html", categories=categories, form_data=request.form)

        filename = save_upload(image)

        listing = Listing(
            title=title,
            description=description,
            price=price,
            category_id=category_id,
            seller_id=current_user.id,
            image_filename=filename,
        )
        db.session.add(listing)
        db.session.commit()
        flash("Listing created successfully.", "success")
        return redirect(url_for("listings.detail", listing_id=listing.id))

    return render_template("listings/create.html", categories=categories, form_data={})
@listings_bp.route("/<int:listing_id>/edit", methods=["GET", "POST"])
@login_required
def edit(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    if listing.seller_id != current_user.id:
        abort(403)  # Authorization check: only the owner may edit

    categories = Category.query.order_by(Category.name).all()

    if request.method == "POST":
        listing.title = request.form.get("title", "").strip()
        listing.description = request.form.get("description", "").strip()
        listing.price = request.form.get("price", type=float) or listing.price
        listing.category_id = request.form.get("category_id", type=int) or listing.category_id

        image = request.files.get("image")
        new_filename = save_upload(image)
        if new_filename:
            listing.image_filename = new_filename

        db.session.commit()
        flash("Listing updated.", "success")
        return redirect(url_for("listings.detail", listing_id=listing.id))

    return render_template("listings/edit.html", listing=listing, categories=categories)


@listings_bp.route("/<int:listing_id>/delete", methods=["POST"])
@login_required
def delete(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    if listing.seller_id != current_user.id:
        abort(403)

    db.session.delete(listing)
    db.session.commit()
    flash("Listing deleted.", "info")
    return redirect(url_for("listings.my_listings"))


@listings_bp.route("/<int:listing_id>/toggle-sold", methods=["POST"])
@login_required
def toggle_sold(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    if listing.seller_id != current_user.id:
        abort(403)

    listing.status = "sold" if listing.status == "available" else "available"
    db.session.commit()
    flash(f"Listing marked as {listing.status}.", "success")
    return redirect(url_for("listings.my_listings"))


@listings_bp.route("/mine")
@login_required
def my_listings():
    listings = Listing.query.filter_by(seller_id=current_user.id).order_by(
        Listing.created_at.desc()
    ).all()
    return render_template("listings/my_listings.html", listings=listings)


@listings_bp.route("/<int:listing_id>/contact", methods=["POST"])
@login_required
def contact_seller(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    body = request.form.get("body", "").strip()

    if listing.seller_id == current_user.id:
        flash("You can't message yourself about your own listing.", "warning")
        return redirect(url_for("listings.detail", listing_id=listing.id))

    if not body:
        flash("Message cannot be empty.", "danger")
        return redirect(url_for("listings.detail", listing_id=listing.id))

    msg = Message(listing_id=listing.id, sender_id=current_user.id, body=body[:1000])
    db.session.add(msg)
    db.session.commit()
    flash("Message sent to seller.", "success")
    return redirect(url_for("listings.detail", listing_id=listing.id))


@listings_bp.route("/messages")
@login_required
def inbox():
    # Messages sent about listings owned by the current user
    messages = (
        Message.query.join(Listing, Message.listing_id == Listing.id)
        .filter(Listing.seller_id == current_user.id)
        .order_by(Message.created_at.desc())
        .all()
    )
    return render_template("listings/inbox.html", messages=messages)
                                                                                                                                                                                             
