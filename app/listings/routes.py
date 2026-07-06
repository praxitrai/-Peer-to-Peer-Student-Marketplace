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
