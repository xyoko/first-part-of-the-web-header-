# app.py
import os
import json
import secrets
from flask import (
    Flask, render_template, request, redirect, session,
    jsonify, url_for, flash, abort
)
from werkzeug.utils import secure_filename
from flask_login import login_user, logout_user, login_required, current_user
from config import Config
from models import User, Recipe, Rating, Comment
from extensions import db, migrate, login_manager, talisman, limiter
from extensions import csrf
from auth import bp as auth_bp
from posts import bp as posts_bp

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config.from_object(Config)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Initialize extensions
db.init_app(app)
migrate.init_app(app, db)
login_manager.init_app(app)
login_manager.login_view = "login"
limiter.init_app(app)
# Initialize Talisman with a reasonable CSP for development; tighten for production
# Allow fonts.googleapis and fonts.gstatic for Google Fonts and cdn.jsdelivr for Bootstrap
# Allow 'data:' in img-src for Bootstrap inline SVG icons (form controls)
talisman.init_app(app, content_security_policy={
    'default-src': ["'self'"],
    'script-src': ["'self'", "'unsafe-inline'", 'https://cdn.jsdelivr.net'],
    'style-src': ["'self'", "'unsafe-inline'", 'https://cdn.jsdelivr.net', 'https://fonts.googleapis.com'],
    'font-src': ["'self'", 'https://fonts.gstatic.com'],
    'img-src': ["'self'", 'data:'],
    'connect-src': ["'self'", 'https://cdn.jsdelivr.net']
})

# Enable CSRF protection for forms
csrf.init_app(app)

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(posts_bp)

# -------------------------
# Simple CSRF protection
# -------------------------
def generate_csrf_token():
    token = secrets.token_urlsafe(32)
    session['csrf_token'] = token
    return token

def validate_csrf(token):
    return token and session.get('csrf_token') and secrets.compare_digest(session.get('csrf_token'), token)

@app.context_processor
def inject_globals():
    # inject csrf token and current_user into templates
    token = session.get('csrf_token') or generate_csrf_token()
    return dict(csrf_token=token, current_user=current_user)

@login_manager.user_loader
def load_user(user_id):
    try:
        return User.query.get(int(user_id))
    except Exception:
        return None

# -------------------------
# Error handlers
# -------------------------
@app.errorhandler(404)
def not_found(e):
    return render_template("errors/404.html"), 404

@app.errorhandler(500)
def server_error(e):
    return render_template("errors/500.html"), 500

# -------------------------
# Home / Index
# -------------------------
@app.route("/")
def index():
    page = request.args.get('page', 1, type=int)
    pagination = Recipe.query.filter_by(approved=True).order_by(Recipe.created_at.desc()).paginate(page=page, per_page=10, error_out=False)
    posts = pagination.items
    return render_template("index.html", posts=posts, pagination=pagination)

# -------------------------
# Search
# -------------------------
from sqlalchemy import or_
@app.route("/search")
def search():
    q = request.args.get("q", "").strip()
    if not q:
        return redirect(url_for('index'))
    like = f"%{q}%"
    results = Recipe.query.filter(
        Recipe.approved == True,
        or_(
            Recipe.title.ilike(like),
            Recipe.description.ilike(like),
            Recipe.ingredients_json.ilike(like),
            Recipe.category.ilike(like)
        )
    ).order_by(Recipe.created_at.desc()).all()
    return render_template("search.html", recipes=results, query=q)

# -------------------------
# Page routes (render templates)
# -------------------------
@app.route("/add-recipe")
@login_required
def add_recipe_page():
    return render_template("add-recipe.html")

@app.route("/my-recipes")
@login_required
def my_recipes_page():
    recipes = Recipe.query.filter_by(user_id=current_user.id).order_by(Recipe.created_at.desc()).all()
    return render_template("my_recipes.html", recipes=recipes)

# Authentication routes are provided by the `auth` blueprint (templates in templates/auth/)

# -------------------------
# Profile
# -------------------------
@app.route("/profile")
@login_required
def profile():
    # Redirect admin users to their special admin dashboard
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    user_recipes = Recipe.query.filter_by(user_id=current_user.id).order_by(Recipe.created_at.desc()).all()
    return render_template("profile.html", user=current_user, recipes=user_recipes)

@app.route("/profile/edit", methods=["POST"])
@login_required
def profile_edit():
    token = request.form.get("csrf_token")
    if not validate_csrf(token):
        flash("Invalid CSRF token", "danger")
        return redirect(url_for('profile'))
    username = request.form.get("username", "").strip()
    bio = request.form.get("bio", "").strip()
    if username:
        current_user.username = username
    current_user.bio = bio
    db.session.commit()
    flash("Profile updated", "success")
    return redirect(url_for('profile'))

# -------------------------
# Recipe creation
# -------------------------
@app.route("/api/recipes/create", methods=["POST"])
@login_required
@csrf.exempt  # Handle CSRF manually or disable for AJAX form submission
def create_recipe():

    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    instructions = request.form.get("instructions", "").strip()
    ingredients = request.form.get("ingredients", "[]")
    category = request.form.get("category", "").strip()
    cooking_time = request.form.get("cooking_time")
    servings = request.form.get("servings")

    # image
    file = request.files.get("image")
    filename = None
    if file and file.filename:
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

    recipe = Recipe(
        title=title,
        description=description,
        instructions=instructions,
        ingredients_json=ingredients,
        image=filename or "",
        category=category,
        cooking_time=int(cooking_time) if cooking_time else None,
        servings=int(servings) if servings else None,
        user_id=current_user.id,
        approved=False
    )

    db.session.add(recipe)
    db.session.commit()
    return jsonify({"success": True, "id": recipe.id})

# -------------------------
# Recipe detail, ratings & comments
# -------------------------
@app.route("/recipe/<int:recipe_id>")
def recipe_view(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    if not recipe.approved and (not current_user.is_authenticated or (not current_user.is_admin and current_user.id != recipe.user_id)):
        abort(404)

    ingredients = []
    try:
        ingredients = json.loads(recipe.ingredients_json or "[]")
    except:
        ingredients = []

    avg = recipe.average_rating()
    # user's rating (if logged in)
    user_rating = None
    if current_user.is_authenticated:
        r = Rating.query.filter_by(user_id=current_user.id, recipe_id=recipe_id).first()
        user_rating = r.score if r else None

    comments = Comment.query.filter_by(recipe_id=recipe_id, is_removed=False).order_by(Comment.created_at.asc()).all()
    return render_template("recipe-detail.html", recipe=recipe, ingredients=ingredients, avg_rating=avg, user_rating=user_rating, comments=comments)

@app.route("/api/recipes/<int:recipe_id>/rate", methods=["POST"])
@login_required
def rate_recipe(recipe_id):
    token = request.form.get("csrf_token") or request.headers.get("X-CSRF-Token")
    if not validate_csrf(token):
        return jsonify({"error": "Invalid CSRF token"}), 400

    score = int(request.form.get("score", 0))
    if score < 1 or score > 5:
        return jsonify({"error": "Invalid score"}), 400

    recipe = Recipe.query.get_or_404(recipe_id)
    # upsert rating
    existing = Rating.query.filter_by(user_id=current_user.id, recipe_id=recipe_id).first()
    if existing:
        existing.score = score
    else:
        new = Rating(score=score, user_id=current_user.id, recipe_id=recipe_id)
        db.session.add(new)
    db.session.commit()
    return jsonify({"success": True, "avg": recipe.average_rating()})

@app.route("/api/recipes/<int:recipe_id>/comment", methods=["POST"])
@login_required
def comment_recipe(recipe_id):
    token = request.form.get("csrf_token") or request.headers.get("X-CSRF-Token")
    if not validate_csrf(token):
        return jsonify({"error": "Invalid CSRF token"}), 400

    body = request.form.get("body", "").strip()
    if not body:
        return jsonify({"error": "Empty comment"}), 400
    recipe = Recipe.query.get_or_404(recipe_id)
    c = Comment(body=body, user_id=current_user.id, recipe_id=recipe_id)
    db.session.add(c)
    db.session.commit()
    return jsonify({
        "success": True,
        "comment": {
            "id": c.id,
            "body": c.body,
            "username": current_user.username,
            "created_at": c.created_at.isoformat()
        }
    })

# -------------------------
# Admin: approve/reject recipe & moderate comments
# -------------------------
@app.route("/admin")
@login_required
def admin_page():
    if not current_user.is_admin:
        return abort(403)
    pending = Recipe.query.filter_by(approved=False).order_by(Recipe.created_at.desc()).all()
    # parse ingredients JSON for templates
    for r in pending:
        try:
            r.ingredients_list = json.loads(r.ingredients_json or '[]')
        except Exception:
            r.ingredients_list = []
    unmoderated_comments = Comment.query.filter_by(is_removed=False).order_by(Comment.created_at.desc()).limit(50).all()
    return render_template("admin.html", pending=pending, comments=unmoderated_comments)

# Admin dashboard page (special profile for admin users)
@app.route("/admin-page")
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        return abort(403)
    pending = Recipe.query.filter_by(approved=False).order_by(Recipe.created_at.desc()).all()
    # parse ingredients JSON for templates
    for r in pending:
        try:
            r.ingredients_list = json.loads(r.ingredients_json or '[]')
        except Exception:
            r.ingredients_list = []
    unmoderated_comments = Comment.query.filter_by(is_removed=False).order_by(Comment.created_at.desc()).limit(50).all()
    return render_template("admin-page.html", pending=pending, comments=unmoderated_comments)

# Primary API endpoints
@app.route("/api/recipes/<int:recipe_id>/approve", methods=["POST"])
@login_required
@csrf.exempt
def api_approve_recipe(recipe_id):
    if not current_user.is_admin:
        return jsonify({"error": "Forbidden"}), 403
    recipe = Recipe.query.get_or_404(recipe_id)
    recipe.approved = True
    db.session.commit()
    return jsonify({"success": True})

@app.route("/api/recipes/<int:recipe_id>/reject", methods=["POST"])
@login_required
@csrf.exempt
def api_reject_recipe(recipe_id):
    if not current_user.is_admin:
        return jsonify({"error": "Forbidden"}), 403
    recipe = Recipe.query.get_or_404(recipe_id)
    db.session.delete(recipe)
    db.session.commit()
    return jsonify({"success": True})

# Aliases to match older front-end JS that calls /recipes/<id>/approve (non-api path)
@app.route("/recipes/<int:recipe_id>/approve", methods=["POST"])
@login_required
def approve_recipe_alias(recipe_id):
    return api_approve_recipe(recipe_id)

@app.route("/recipes/<int:recipe_id>/reject", methods=["POST"])
@login_required
def reject_recipe_alias(recipe_id):
    return api_reject_recipe(recipe_id)

@app.route("/api/comments/<int:comment_id>/remove", methods=["POST"])
@login_required
def api_remove_comment(comment_id):
    if not current_user.is_admin:
        return jsonify({"error": "Forbidden"}), 403
    comment = Comment.query.get_or_404(comment_id)
    comment.is_removed = True
    db.session.commit()
    return jsonify({"success": True})

@app.route("/api/comments/<int:comment_id>/restore", methods=["POST"])
@login_required
def api_restore_comment(comment_id):
    if not current_user.is_admin:
        return jsonify({"error": "Forbidden"}), 403
    comment = Comment.query.get_or_404(comment_id)
    comment.is_removed = False
    db.session.commit()
    return jsonify({"success": True})

# -------------------------
# Initialize DB & run
# -------------------------
if __name__ == "__main__":
    with app.app_context():
        # create tables if missing
        db.create_all()
    app.run(debug=True)
