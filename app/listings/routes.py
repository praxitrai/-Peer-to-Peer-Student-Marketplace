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

