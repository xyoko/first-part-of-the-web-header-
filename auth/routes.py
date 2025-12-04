from flask import render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_user, logout_user, login_required
from . import bp
from models import User
from extensions import db, limiter, csrf


# Exempt auth routes from CSRF protection (they handle auth manually)
@csrf.exempt
@bp.route('/login', methods=['GET', 'POST'])
@limiter.limit('10/hour')
def login():
    if request.method == 'GET':
        return render_template('auth/login.html')
    
    # POST - Handle login
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    
    # Validate input
    if not username:
        error = 'Username or email is required'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': error}), 400
        flash(error, 'danger')
        return render_template('auth/login.html')
    
    if not password:
        error = 'Password is required'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': error}), 400
        flash(error, 'danger')
        return render_template('auth/login.html')
    
    # Find user by username or email
    user = User.query.filter((User.username == username) | (User.email == username)).first()
    
    if not user or not user.check_password(password):
        error = 'Invalid credentials'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': error}), 400
        flash(error, 'danger')
        return render_template('auth/login.html')
    
    # Login successful
    login_user(user)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True, 'redirect': url_for('profile')})
    
    flash('Logged in successfully', 'success')
    return redirect(url_for('index'))


@csrf.exempt
@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('auth/register.html')
    
    # POST - Handle registration
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '').strip()
    
    # Validate input
    errors = {}
    if not username:
        errors['username'] = 'Username is required'
    elif len(username) < 3:
        errors['username'] = 'Username must be at least 3 characters'
    elif len(username) > 80:
        errors['username'] = 'Username must be at most 80 characters'
    
    if not email:
        errors['email'] = 'Email is required'
    elif '@' not in email or len(email) > 200:
        errors['email'] = 'Invalid email address'
    
    if not password:
        errors['password'] = 'Password is required'
    elif len(password) < 6:
        errors['password'] = 'Password must be at least 6 characters'
    
    # Check if user already exists
    if not errors:
        existing = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing:
            if existing.username == username:
                errors['username'] = 'Username already exists'
            if existing.email == email:
                errors['email'] = 'Email already exists'
    
    if errors:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': 'Validation failed', 'errors': {k: [v] for k, v in errors.items()}}), 400
        for field, msg in errors.items():
            flash(f"{field}: {msg}", 'warning')
        return render_template('auth/register.html')
    
    # Create new user
    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    login_user(user)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True, 'redirect': url_for('profile')})
    
    flash('Account created successfully', 'success')
    return redirect(url_for('index'))


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))
