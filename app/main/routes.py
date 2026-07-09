from flask import Blueprint, render_template, session
from app.models import Listing

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    latest = (
        Listing.query.filter_by(status="available")
        .order_by(Listing.created_at.desc())
        .limit(8)
        .all()
    )

    recent_ids = session.get("recently_viewed", [])
    recently_viewed = []
    if recent_ids:
        found = {l.id: l for l in Listing.query.filter(Listing.id.in_(recent_ids)).all()}
        recently_viewed = [found[i] for i in recent_ids if i in found]

    return render_template("index.html", latest=latest, recently_viewed=recently_viewed)
                                                                                           
