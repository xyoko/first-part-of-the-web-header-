import os
import json
from flask import render_template, redirect, url_for, flash, request, current_app, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from . import bp
from .forms import RecipeForm
from models import Recipe
from extensions import db, limiter

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
        return redirect(url_for('posts.create'))
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
            if file.filename and allowed_file(file.filename):
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
def delete(id):
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
    return render_template('posts/view.html', post=recipe)
