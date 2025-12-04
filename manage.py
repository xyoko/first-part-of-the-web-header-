import click
from app import app
from models import db, User

@app.cli.command('create-admin')
@click.argument('username')
@click.argument('email')
@click.argument('password')
def create_admin(username, email, password):
    """Create an admin user."""
    with app.app_context():
        if User.query.filter_by(username=username).first():
            print('User already exists')
            return
        u = User(username=username, email=email, is_admin=True)
        u.set_password(password)
        db.session.add(u)
        db.session.commit()
        print('Admin user created.')
