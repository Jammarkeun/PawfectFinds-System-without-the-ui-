from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename
from sqlalchemy import and_, or_, func
from app import db
from app.models.models import Product, ProductImage, OrderItem, Order, Category, Notification, User
from app.utils.auth import role_required, get_current_user
import os
import uuid
from datetime import datetime, timedelta

seller_bp = Blueprint('seller', __name__)

@seller_bp.route('/dashboard')
@role_required('seller')
def dashboard():
    """Seller dashboard"""
    user = get_current_user()
    
    # Get dashboard statistics
    total_products = Product.query.filter_by(seller_id=user.id).count()
    active_products = Product.query.filter_by(seller_id=user.id, status='active').count()
    
    # Get recent orders
    recent_orders = OrderItem.query.filter_by(seller_id=user.id).join(Order).order_by(
        Order.created_at.desc()
    ).limit(10).all()
    
    # Get pending orders
    pending_orders = OrderItem.query.filter_by(
        seller_id=user.id, 
        status='pending'
    ).count()
    
    # Calculate monthly sales
    thirty_days_ago = datetime.now() - timedelta(days=30)
    monthly_sales = db.session.query(func.sum(OrderItem.total_price)).filter(
        OrderItem.seller_id == user.id,
        OrderItem.created_at >= thirty_days_ago
    ).scalar() or 0
    
    # Get low stock products
    low_stock_products = Product.query.filter(
        Product.seller_id == user.id,
        Product.stock_quantity <= 5,
        Product.status == 'active'
    ).all()
    
    return render_template('seller/dashboard.html',
                         total_products=total_products,
                         active_products=active_products,
                         recent_orders=recent_orders,
                         pending_orders=pending_orders,
                         monthly_sales=monthly_sales,
                         low_stock_products=low_stock_products)

@seller_bp.route('/products')
@role_required('seller')
def products():
    """Seller products"""
    user = get_current_user()
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    status = request.args.get('status', '')
    
    # Base query
    query = Product.query.filter_by(seller_id=user.id)
    
    # Apply filters
    if search:
        query = query.filter(
            or_(
                Product.name.ilike(f'%{search}%'),
                Product.description.ilike(f'%{search}%'),
                Product.sku.ilike(f'%{search}%')
            )
        )
    
    if status:
        query = query.filter_by(status=status)
    
    # Paginate
    products_paginated = query.order_by(Product.created_at.desc()).paginate(
        page=page, per_page=12, error_out=False
    )
    
    return render_template('seller/products.html',
                         products=products_paginated.items,
                         pagination=products_paginated,
                         search=search,
                         status_filter=status)

@seller_bp.route('/product/add', methods=['GET', 'POST'])
@role_required('seller')
def add_product():
    """Add new product"""
    user = get_current_user()
    
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        category_id = request.form.get('category_id', type=int)
        price = request.form.get('price', type=float)
        stock_quantity = request.form.get('stock_quantity', type=int)
        sku = request.form.get('sku', '').strip()
        weight = request.form.get('weight', type=float)
        dimensions = request.form.get('dimensions', '').strip()
        brand = request.form.get('brand', '').strip()
        age_group = request.form.get('age_group', 'all_ages')
        pet_type = request.form.get('pet_type')
        
        # Validation
        errors = []
        
        if not name:
            errors.append('Product name is required.')
        
        if not category_id:
            errors.append('Category is required.')
        
        if not price or price <= 0:
            errors.append('Valid price is required.')
        
        if not stock_quantity or stock_quantity < 0:
            errors.append('Valid stock quantity is required.')
        
        if not pet_type:
            errors.append('Pet type is required.')
        
        # Check if SKU already exists
        if sku:
            existing_sku = Product.query.filter_by(sku=sku).first()
            if existing_sku:
                errors.append('SKU already exists.')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            categories = Category.query.filter_by(status='active').all()
            return render_template('seller/add_product.html', categories=categories)
        
        try:
            # Create product
            product = Product(
                seller_id=user.id,
                category_id=category_id,
                name=name,
                description=description,
                price=price,
                stock_quantity=stock_quantity,
                sku=sku or None,
                weight=weight,
                dimensions=dimensions,
                brand=brand,
                age_group=age_group,
                pet_type=pet_type,
                status='active'
            )
            
            db.session.add(product)
            db.session.flush()  # Get product ID
            
            # Handle image uploads
            uploaded_files = request.files.getlist('images')
            if uploaded_files and uploaded_files[0].filename:
                from config.config import Config
                upload_folder = os.path.join(Config.UPLOAD_FOLDER, 'products')
                
                for i, file in enumerate(uploaded_files[:5]):  # Max 5 images
                    if file and file.filename:
                        # Generate unique filename
                        filename = f"{product.id}_{uuid.uuid4().hex[:8]}_{secure_filename(file.filename)}"
                        file_path = os.path.join(upload_folder, filename)
                        
                        file.save(file_path)
                        
                        # Create product image record
                        product_image = ProductImage(
                            product_id=product.id,
                            image_url=f'/static/uploads/products/{filename}',
                            is_primary=(i == 0),  # First image is primary
                            alt_text=f"{name} image"
                        )
                        db.session.add(product_image)
            
            db.session.commit()
            flash('Product added successfully!', 'success')
            return redirect(url_for('seller.products'))
            
        except Exception as e:
            db.session.rollback()
            flash('Failed to add product. Please try again.', 'error')
    
    categories = Category.query.filter_by(status='active').all()
    return render_template('seller/add_product.html', categories=categories)

@seller_bp.route('/product/edit/<int:product_id>', methods=['GET', 'POST'])
@role_required('seller')
def edit_product(product_id):
    """Edit product"""
    user = get_current_user()
    product = Product.query.filter_by(
        id=product_id,
        seller_id=user.id
    ).first_or_404()
    
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        category_id = request.form.get('category_id', type=int)
        price = request.form.get('price', type=float)
        stock_quantity = request.form.get('stock_quantity', type=int)
        sku = request.form.get('sku', '').strip()
        weight = request.form.get('weight', type=float)
        dimensions = request.form.get('dimensions', '').strip()
        brand = request.form.get('brand', '').strip()
        age_group = request.form.get('age_group', 'all_ages')
        pet_type = request.form.get('pet_type')
        status = request.form.get('status', 'active')
        
        # Validation
        errors = []
        
        if not name:
            errors.append('Product name is required.')
        
        if not category_id:
            errors.append('Category is required.')
        
        if not price or price <= 0:
            errors.append('Valid price is required.')
        
        if not stock_quantity or stock_quantity < 0:
            errors.append('Valid stock quantity is required.')
        
        if not pet_type:
            errors.append('Pet type is required.')
        
        # Check if SKU already exists (exclude current product)
        if sku:
            existing_sku = Product.query.filter(
                Product.sku == sku,
                Product.id != product_id
            ).first()
            if existing_sku:
                errors.append('SKU already exists.')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            categories = Category.query.filter_by(status='active').all()
            return render_template('seller/edit_product.html', 
                                 product=product, categories=categories)
        
        try:
            # Update product
            product.name = name
            product.description = description
            product.category_id = category_id
            product.price = price
            product.stock_quantity = stock_quantity
            product.sku = sku or None
            product.weight = weight
            product.dimensions = dimensions
            product.brand = brand
            product.age_group = age_group
            product.pet_type = pet_type
            product.status = status
            
            # Handle new image uploads
            uploaded_files = request.files.getlist('new_images')
            if uploaded_files and uploaded_files[0].filename:
                from config.config import Config
                upload_folder = os.path.join(Config.UPLOAD_FOLDER, 'products')
                
                for file in uploaded_files[:5]:  # Max 5 additional images
                    if file and file.filename:
                        # Generate unique filename
                        filename = f"{product.id}_{uuid.uuid4().hex[:8]}_{secure_filename(file.filename)}"
                        file_path = os.path.join(upload_folder, filename)
                        
                        file.save(file_path)
                        
                        # Create product image record
                        product_image = ProductImage(
                            product_id=product.id,
                            image_url=f'/static/uploads/products/{filename}',
                            is_primary=False,
                            alt_text=f"{name} image"
                        )
                        db.session.add(product_image)
            
            db.session.commit()
            flash('Product updated successfully!', 'success')
            return redirect(url_for('seller.products'))
            
        except Exception as e:
            db.session.rollback()
            flash('Failed to update product. Please try again.', 'error')
    
    categories = Category.query.filter_by(status='active').all()
    return render_template('seller/edit_product.html', 
                         product=product, categories=categories)

@seller_bp.route('/product/delete/<int:product_id>', methods=['POST'])
@role_required('seller')
def delete_product(product_id):
    """Delete product"""
    user = get_current_user()
    product = Product.query.filter_by(
        id=product_id,
        seller_id=user.id
    ).first_or_404()
    
    # Check if product has orders
    has_orders = OrderItem.query.filter_by(product_id=product_id).first()
    
    try:
        if has_orders:
            # Soft delete - just mark as inactive
            product.status = 'inactive'
            flash('Product marked as inactive (has existing orders).', 'warning')
        else:
            # Hard delete
            db.session.delete(product)
            flash('Product deleted successfully!', 'success')
        
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash('Failed to delete product.', 'error')
    
    return redirect(url_for('seller.products'))

@seller_bp.route('/orders')
@role_required('seller')
def orders():
    """Seller orders"""
    user = get_current_user()
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    
    # Base query
    query = OrderItem.query.filter_by(seller_id=user.id).join(Order)
    
    # Apply status filter
    if status:
        query = query.filter(OrderItem.status == status)
    
    # Paginate
    order_items_paginated = query.order_by(Order.created_at.desc()).paginate(
        page=page, per_page=15, error_out=False
    )
    
    return render_template('seller/orders.html',
                         order_items=order_items_paginated.items,
                         pagination=order_items_paginated,
                         status_filter=status)

@seller_bp.route('/order/<int:order_item_id>')
@role_required('seller')
def order_detail(order_item_id):
    """Order item detail"""
    user = get_current_user()
    order_item = OrderItem.query.filter_by(
        id=order_item_id,
        seller_id=user.id
    ).first_or_404()
    
    return render_template('seller/order_detail.html', order_item=order_item)

@seller_bp.route('/update-order-status', methods=['POST'])
@role_required('seller')
def update_order_status():
    """Update order item status"""
    user = get_current_user()
    order_item_id = request.form.get('order_item_id', type=int)
    new_status = request.form.get('status')
    
    if not order_item_id or not new_status:
        flash('Invalid data.', 'error')
        return redirect(url_for('seller.orders'))
    
    order_item = OrderItem.query.filter_by(
        id=order_item_id,
        seller_id=user.id
    ).first_or_404()
    
    valid_statuses = ['pending', 'confirmed', 'preparing', 'shipped', 'delivered', 'cancelled']
    if new_status not in valid_statuses:
        flash('Invalid status.', 'error')
        return redirect(url_for('seller.order_detail', order_item_id=order_item_id))
    
    try:
        order_item.status = new_status
        
        # Create notification for customer
        status_messages = {
            'confirmed': 'Your order has been confirmed by the seller.',
            'preparing': 'Your order is being prepared for shipment.',
            'shipped': 'Your order has been shipped.',
            'delivered': 'Your order has been delivered.',
            'cancelled': 'Your order has been cancelled by the seller.'
        }
        
        if new_status in status_messages:
            notification = Notification(
                user_id=order_item.order.user_id,
                type='order_status',
                title=f'Order Status Update - {order_item.order.order_number}',
                message=status_messages[new_status],
                related_id=order_item.order_id
            )
            db.session.add(notification)
        
        db.session.commit()
        flash('Order status updated successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('Failed to update order status.', 'error')
    
    return redirect(url_for('seller.order_detail', order_item_id=order_item_id))

@seller_bp.route('/profile')
@role_required('seller')
def profile():
    """Seller profile"""
    user = get_current_user()
    return render_template('seller/profile.html', user=user)

@seller_bp.route('/update-profile', methods=['POST'])
@role_required('seller')
def update_profile():
    """Update seller profile"""
    user = get_current_user()
    
    # Get form data
    first_name = request.form.get('first_name', '').strip()
    last_name = request.form.get('last_name', '').strip()
    phone = request.form.get('phone', '').strip()
    address = request.form.get('address', '').strip()
    city = request.form.get('city', '').strip()
    state = request.form.get('state', '').strip()
    zip_code = request.form.get('zip_code', '').strip()
    
    # Validation
    if not first_name or not last_name:
        flash('First name and last name are required.', 'error')
        return redirect(url_for('seller.profile'))
    
    try:
        # Update user
        user.first_name = first_name
        user.last_name = last_name
        user.phone = phone
        user.address = address
        user.city = city
        user.state = state
        user.zip_code = zip_code
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Failed to update profile.', 'error')
    
    return redirect(url_for('seller.profile'))

@seller_bp.route('/analytics')
@role_required('seller')
def analytics():
    """Seller analytics"""
    user = get_current_user()
    
    # Get date range from query params
    days = request.args.get('days', 30, type=int)
    start_date = datetime.now() - timedelta(days=days)
    
    # Sales analytics
    sales_data = db.session.query(
        func.date(OrderItem.created_at).label('date'),
        func.sum(OrderItem.total_price).label('total_sales'),
        func.count(OrderItem.id).label('order_count')
    ).filter(
        OrderItem.seller_id == user.id,
        OrderItem.created_at >= start_date
    ).group_by(func.date(OrderItem.created_at)).all()
    
    # Top products
    top_products = db.session.query(
        Product.name,
        func.sum(OrderItem.quantity).label('total_sold'),
        func.sum(OrderItem.total_price).label('total_revenue')
    ).join(OrderItem).filter(
        Product.seller_id == user.id,
        OrderItem.created_at >= start_date
    ).group_by(Product.id, Product.name).order_by(
        func.sum(OrderItem.total_price).desc()
    ).limit(10).all()
    
    # Order status distribution
    order_status = db.session.query(
        OrderItem.status,
        func.count(OrderItem.id).label('count')
    ).filter(
        OrderItem.seller_id == user.id,
        OrderItem.created_at >= start_date
    ).group_by(OrderItem.status).all()
    
    return render_template('seller/analytics.html',
                         sales_data=sales_data,
                         top_products=top_products,
                         order_status=order_status,
                         days=days)