import os
import json
from flask import render_template, redirect, url_for, flash, request, current_app, abort, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from . import bp
from .forms import RecipeForm, CommentForm, RatingForm
from models import Recipe, Comment, Rating
from extensions import db, limiter, csrf

ALLOWED_EXT = {'png', 'jpg', 'jpeg', 'gif'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXT


@bp.route('/create', methods=['GET', 'POST'], endpoint='create_post')
@login_required
@limiter.limit('30/hour')
def create():
    form = RecipeForm()
    if form.validate_on_submit():
        title = form.title.data.strip()
        description = form.description.data.strip() if form.description.data else ''
        instructions = form.instructions.data or ''
        ingredients_raw = form.ingredients.data or ''
        # try to parse ingredients as JSON, otherwise split by newline
        try:
            ingredients_json = json.dumps(json.loads(ingredients_raw)) if ingredients_raw.strip().startswith('[') else json.dumps([i.strip() for i in ingredients_raw.splitlines() if i.strip()])
        except Exception:
            ingredients_json = json.dumps([i.strip() for i in ingredients_raw.splitlines() if i.strip()])

        filename = ''
        if form.image.data:
            file = form.image.data
            if file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                upload_folder = current_app.config.get('UPLOAD_FOLDER', 'static/uploads')
                os.makedirs(upload_folder, exist_ok=True)
                file.save(os.path.join(upload_folder, filename))

        recipe = Recipe(
            title=title,
            description=description,
            instructions=instructions,
            ingredients_json=ingredients_json,
            image=filename,
            category=form.category.data or '',
            cooking_time=form.cooking_time.data,
            servings=form.servings.data,
            user_id=current_user.id,
            approved=False,
        )
        db.session.add(recipe)
        db.session.commit()
        flash('Recipe created, pending approval', 'success')
        # If request originated from AJAX (our create page uses fetch), return JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'redirect': url_for('profile')})
        return redirect(url_for('posts.create'))
    # If the form wasn't valid and this was an AJAX POST, return errors
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'error': 'Validation failed', 'errors': form.errors}), 400

    return render_template('posts/create.html', form=form)


@bp.route('/<int:id>/edit', methods=['GET', 'POST'], endpoint='edit_post')
@login_required
def edit(id):
    recipe = Recipe.query.get_or_404(id)
    if recipe.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    form = RecipeForm(obj=recipe)
    if form.validate_on_submit():
        recipe.title = form.title.data.strip()
        recipe.description = form.description.data or ''
        recipe.instructions = form.instructions.data or ''
        ingredients_raw = form.ingredients.data or ''
        try:
            recipe.ingredients_json = json.dumps(json.loads(ingredients_raw)) if ingredients_raw.strip().startswith('[') else json.dumps([i.strip() for i in ingredients_raw.splitlines() if i.strip()])
        except Exception:
            recipe.ingredients_json = json.dumps([i.strip() for i in ingredients_raw.splitlines() if i.strip()])

        if form.image.data:
            file = form.image.data
            # If a new file was uploaded, `file` will be a FileStorage with a `filename` attribute.
            # In some cases (prefilled form), `form.image.data` may be a string filename — handle gracefully.
            if hasattr(file, 'filename') and file.filename:
                if allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'static/uploads')
                    os.makedirs(upload_folder, exist_ok=True)
                    file.save(os.path.join(upload_folder, filename))
                    recipe.image = filename

        recipe.category = form.category.data or ''
        recipe.cooking_time = form.cooking_time.data
        recipe.servings = form.servings.data
        db.session.commit()
        flash('Recipe updated', 'success')
        return redirect(url_for('posts.view_post', id=recipe.id))
    # prefill ingredients for form display
    try:
        ingr = json.loads(recipe.ingredients_json or '[]')
        form.ingredients.data = '\n'.join(ingr) if isinstance(ingr, list) else recipe.ingredients_json
    except Exception:
        form.ingredients.data = recipe.ingredients_json
    return render_template('posts/edit.html', form=form, recipe=recipe)


@bp.route('/<int:id>/delete', methods=['POST'], endpoint='delete_post')
@login_required
@csrf.exempt
def delete(id):
    # Validate CSRF token manually since we exempted this route
    from flask_wtf.csrf import validate_csrf as fw_validate_csrf
    token = request.form.get("csrf_token")
    try:
        fw_validate_csrf(token)
    except Exception:
        flash("Invalid CSRF token", "danger")
        return redirect(url_for('index'))
    
    recipe = Recipe.query.get_or_404(id)
    if recipe.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    db.session.delete(recipe)
    db.session.commit()
    flash('Recipe deleted', 'info')
    return redirect(url_for('index'))


@bp.route('/<int:id>', methods=['GET'], endpoint='view_post')
def view(id):
    recipe = Recipe.query.get_or_404(id)
    # only show unapproved recipes to their owners or admins
    if not recipe.approved and (not current_user.is_authenticated or (not current_user.is_admin and current_user.id != recipe.user_id)):
        abort(404)
    
    comment_form = CommentForm()
    rating_form = RatingForm()
    
    return render_template('posts/view.html', post=recipe, comment_form=comment_form, rating_form=rating_form)


@bp.route('/<int:id>/rate', methods=['POST'], endpoint='rate_recipe')
@login_required
def rate_recipe(id):
    recipe = Recipe.query.get_or_404(id)
    form = RatingForm()
    
    if form.validate_on_submit():
        # Check if user already rated this recipe
        existing_rating = Rating.query.filter_by(user_id=current_user.id, recipe_id=id).first()
        
        if existing_rating:
            existing_rating.score = form.score.data
            flash('Your rating has been updated', 'success')
        else:
            rating = Rating(score=form.score.data, user_id=current_user.id, recipe_id=id)
            db.session.add(rating)
            flash('Thank you for rating this recipe!', 'success')
        
        db.session.commit()
    
    return redirect(url_for('posts.view_post', id=id))


@bp.route('/<int:id>/comment', methods=['POST'], endpoint='add_comment')
@login_required
def add_comment(id):
    recipe = Recipe.query.get_or_404(id)
    form = CommentForm()
    
    if form.validate_on_submit():
        comment = Comment(body=form.body.data, user_id=current_user.id, recipe_id=id)
        db.session.add(comment)
        db.session.commit()
        flash('Your comment has been posted!', 'success')
    else:
        flash('Please enter a valid comment', 'danger')
    
    return redirect(url_for('posts.view_post', id=id))


@bp.route('/comment/<int:comment_id>/delete', methods=['POST'], endpoint='delete_comment')
@login_required
@csrf.exempt
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    recipe_id = comment.recipe_id
    
    # Check if user is comment owner or admin
    if comment.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    
    comment.is_removed = True
    db.session.commit()
    flash('Comment deleted', 'info')
    
    return redirect(url_for('posts.view_post', id=recipe_id))

