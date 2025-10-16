from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from app import db

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    city = db.Column(db.String(50))
    state = db.Column(db.String(50))
    zip_code = db.Column(db.String(10))
    role = db.Column(db.Enum('customer', 'seller', 'admin', 'rider', name='user_roles'), default='customer')
    status = db.Column(db.Enum('active', 'inactive', 'suspended', name='user_status'), default='active')
    profile_image = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    products = db.relationship('Product', backref='seller', lazy='dynamic')
    orders = db.relationship('Order', foreign_keys='Order.user_id', backref='customer', lazy='dynamic')
    delivery_orders = db.relationship('Order', foreign_keys='Order.rider_id', backref='rider', lazy='dynamic')
    reviews = db.relationship('Review', backref='reviewer', lazy='dynamic')
    cart_items = db.relationship('CartItem', backref='user', lazy='dynamic')
    seller_application = db.relationship('SellerApplication', foreign_keys='SellerApplication.user_id', backref='applicant', lazy='dynamic')
    notifications = db.relationship('Notification', backref='user', lazy='dynamic')
    rider_performance = db.relationship('RiderPerformance', foreign_keys='RiderPerformance.rider_id', backref='rider_profile', lazy='dynamic')
    rider_earnings = db.relationship('RiderEarning', backref='rider', lazy='dynamic')
    wishlist_items = db.relationship('Wishlist', backref='user', lazy='dynamic')
    system_logs = db.relationship('SystemLog', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def __repr__(self):
        return f'<User {self.username}>'

class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    image = db.Column(db.String(255))
    parent_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    status = db.Column(db.Enum('active', 'inactive', name='category_status'), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Self-referential relationship
    subcategories = db.relationship('Category', backref=db.backref('parent', remote_side=[id]))
    products = db.relationship('Product', backref='category', lazy='dynamic')
    
    def __repr__(self):
        return f'<Category {self.name}>'

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    seller_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    stock_quantity = db.Column(db.Integer, nullable=False, default=0)
    sku = db.Column(db.String(50), unique=True)
    weight = db.Column(db.Numeric(8, 2))
    dimensions = db.Column(db.String(50))
    brand = db.Column(db.String(100))
    age_group = db.Column(db.Enum('puppy', 'adult', 'senior', 'all_ages', name='age_groups'), default='all_ages')
    pet_type = db.Column(db.Enum('dog', 'cat', 'fish', 'bird', 'other', name='pet_types'), nullable=False)
    status = db.Column(db.Enum('active', 'inactive', 'out_of_stock', name='product_status'), default='active')
    featured = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    images = db.relationship('ProductImage', backref='product', lazy='dynamic', cascade='all, delete-orphan')
    cart_items = db.relationship('CartItem', backref='product', lazy='dynamic')
    order_items = db.relationship('OrderItem', backref='product', lazy='dynamic')
    reviews = db.relationship('Review', backref='product', lazy='dynamic')
    wishlist_items = db.relationship('Wishlist', backref='product', lazy='dynamic')
    
    def get_primary_image(self):
        primary_image = self.images.filter_by(is_primary=True).first()
        return primary_image.image_url if primary_image else '/static/img/placeholder.png'
    
    def get_average_rating(self):
        reviews = self.reviews.filter_by(status='approved').all()
        if reviews:
            return sum([review.rating for review in reviews]) / len(reviews)
        return 0
    
    def is_in_stock(self):
        return self.stock_quantity > 0 and self.status == 'active'
    
    def __repr__(self):
        return f'<Product {self.name}>'

class ProductImage(db.Model):
    __tablename__ = 'product_images'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    image_url = db.Column(db.String(255), nullable=False)
    is_primary = db.Column(db.Boolean, default=False)
    alt_text = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ProductImage {self.image_url}>'

class CartItem(db.Model):
    __tablename__ = 'cart'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'product_id', name='unique_user_product'),)
    
    def get_total_price(self):
        return float(self.product.price) * self.quantity
    
    def __repr__(self):
        return f'<CartItem User:{self.user_id} Product:{self.product_id}>'

class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.Enum('pending', 'confirmed', 'preparing', 'shipped', 'out_for_delivery', 'delivered', 'cancelled', 'refunded', name='order_status'), default='pending')
    payment_method = db.Column(db.Enum('cash_on_delivery', 'credit_card', 'paypal', 'bank_transfer', name='payment_methods'), default='cash_on_delivery')
    payment_status = db.Column(db.Enum('pending', 'paid', 'failed', 'refunded', name='payment_status'), default='pending')
    shipping_address = db.Column(db.Text, nullable=False)
    billing_address = db.Column(db.Text)
    notes = db.Column(db.Text)
    rider_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    delivered_at = db.Column(db.DateTime)
    
    # Relationships
    order_items = db.relationship('OrderItem', backref='order', lazy='dynamic', cascade='all, delete-orphan')
    rider_earnings = db.relationship('RiderEarning', backref='order', lazy='dynamic')
    rider_performance = db.relationship('RiderPerformance', backref='order', lazy='dynamic')
    
    def __repr__(self):
        return f'<Order {self.order_number}>'

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    total_price = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.Enum('pending', 'confirmed', 'preparing', 'shipped', 'delivered', 'cancelled', name='order_item_status'), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    seller = db.relationship('User', foreign_keys=[seller_id])
    reviews = db.relationship('Review', backref='order_item', lazy='dynamic')
    
    def __repr__(self):
        return f'<OrderItem {self.order_id}-{self.product_id}>'

class Review(db.Model):
    __tablename__ = 'reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    order_item_id = db.Column(db.Integer, db.ForeignKey('order_items.id'))
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    status = db.Column(db.Enum('pending', 'approved', 'rejected', name='review_status'), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'product_id', 'order_item_id', name='unique_user_product_order'),
        db.CheckConstraint('rating >= 1 AND rating <= 5', name='rating_range')
    )
    
    def __repr__(self):
        return f'<Review {self.user_id}-{self.product_id}>'

class SellerApplication(db.Model):
    __tablename__ = 'seller_applications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    business_name = db.Column(db.String(200), nullable=False)
    business_description = db.Column(db.Text)
    business_address = db.Column(db.Text, nullable=False)
    tax_id = db.Column(db.String(50))
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    documents = db.Column(db.Text)  # JSON array of document URLs
    status = db.Column(db.Enum('pending', 'approved', 'rejected', 'under_review', name='application_status'), default='pending')
    admin_notes = db.Column(db.Text)
    reviewed_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    reviewed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    reviewer = db.relationship('User', foreign_keys=[reviewed_by])
    
    def __repr__(self):
        return f'<SellerApplication {self.business_name}>'

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    type = db.Column(db.Enum('order_status', 'seller_application', 'product_review', 'delivery_update', 'general', name='notification_types'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    related_id = db.Column(db.Integer)  # Can reference order_id, application_id, etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Notification {self.title}>'

class RiderPerformance(db.Model):
    __tablename__ = 'rider_performance'
    
    id = db.Column(db.Integer, primary_key=True)
    rider_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    rating = db.Column(db.Integer)
    feedback = db.Column(db.Text)
    delivery_time_minutes = db.Column(db.Integer)
    rated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    rater = db.relationship('User', foreign_keys=[rated_by])
    
    __table_args__ = (db.CheckConstraint('rating >= 1 AND rating <= 5', name='performance_rating_range'),)
    
    def __repr__(self):
        return f'<RiderPerformance {self.rider_id}-{self.order_id}>'

class RiderEarning(db.Model):
    __tablename__ = 'rider_earnings'
    
    id = db.Column(db.Integer, primary_key=True)
    rider_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    base_fee = db.Column(db.Numeric(8, 2), nullable=False)
    distance_fee = db.Column(db.Numeric(8, 2), default=0)
    tip_amount = db.Column(db.Numeric(8, 2), default=0)
    total_earning = db.Column(db.Numeric(8, 2), nullable=False)
    status = db.Column(db.Enum('pending', 'paid', name='earning_status'), default='pending')
    paid_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<RiderEarning {self.rider_id}-{self.order_id}>'

class WebsiteSetting(db.Model):
    __tablename__ = 'website_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    setting_key = db.Column(db.String(100), unique=True, nullable=False)
    setting_value = db.Column(db.Text)
    description = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<WebsiteSetting {self.setting_key}>'

class Wishlist(db.Model):
    __tablename__ = 'wishlist'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'product_id', name='unique_user_product_wish'),)
    
    def __repr__(self):
        return f'<Wishlist {self.user_id}-{self.product_id}>'

class SystemLog(db.Model):
    __tablename__ = 'system_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<SystemLog {self.action}>'