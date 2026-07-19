"""
RetailMind AI - Database Initialization & Seeding
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from werkzeug.security import generate_password_hash
from models import db, User, Category


def seed_database(app):
    """Seed the database with initial data."""
    with app.app_context():
        db.create_all()
        
        # Create default admin user if not exists
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                password_hash=generate_password_hash('admin123'),
                role='admin'
            )
            db.session.add(admin)
            print('[Seed] Created default admin user (admin/admin123)')
        
        # Create default categories if none exist
        if Category.query.count() == 0:
            categories = [
                Category(name='Rice & Grains', description='Rice, wheat, and other grains'),
                Category(name='Cooking Oil', description='Cooking oils and ghee'),
                Category(name='Spices', description='Spices and masala'),
                Category(name='Beverages', description='Tea, coffee, and soft drinks'),
                Category(name='Dairy', description='Milk, butter, cheese, and yogurt'),
                Category(name='Snacks', description='Chips, biscuits, and namkeen'),
                Category(name='Personal Care', description='Soaps, shampoos, and cosmetics'),
                Category(name='Household', description='Cleaning and household items'),
                Category(name='Fruits & Vegetables', description='Fresh produce'),
                Category(name='Bakery', description='Bread, cakes, and pastries'),
            ]
            db.session.add_all(categories)
            print(f'[Seed] Created {len(categories)} default categories')
        
        db.session.commit()
        print('[Seed] Database seeded successfully!')


if __name__ == '__main__':
    from app import create_app
    app = create_app()
    seed_database(app)
