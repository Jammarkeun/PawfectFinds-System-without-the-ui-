from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from app.utils.decorators import login_required, seller_required
from app.models.user import User
from app.models.product import Product
from app.models.order import Order
from app.models.seller_request import SellerRequest
from app.services.database import Database
from app.forms import SellerProductForm, OrderStatusForm, SellerApplicationForm
from app.models.delivery import Delivery
from datetime import datetime, timedelta

seller_bp = Blueprint('seller', __name__)

@seller_bp.route('/dashboard')
@login_required
@seller_required
def dashboard():
    seller_id = session['user_id']
    seller = User.get_by_id(seller_id)
    
    # Seller statistics
    db = Database()
    
    # Product stats
    product_stats = db.execute_query("""
        SELECT 
            COUNT(*) as total_products,
            SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active_products,
            SUM(CASE WHEN stock_quantity = 0 THEN 1 ELSE 0 END) as out_of_stock
        FROM products WHERE seller_id = %s
    """, (seller_id,), fetch=True, fetchone=True)
    
    # Order stats
    order_stats = db.execute_query("""
        SELECT 
            COUNT(*) as total_orders,
            SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending_orders,
            SUM(CASE WHEN status = 'delivered' THEN 1 ELSE 0 END) as delivered_orders,
            SUM(total_amount) as total_revenue
        FROM orders WHERE seller_id = %s
    """, (seller_id,), fetch=True, fetchone=True)
    
    # All products
    products = Product.list(seller_id=seller_id, status=None)
    
    # Recent orders
    recent_orders = Order.list_for_seller(seller_id, limit=10)
    
    # Top selling products
    top_products = db.execute_query("""
        SELECT p.name, p.price, COUNT(oi.id) as orders_count, SUM(oi.quantity) as total_sold
        FROM products p
        LEFT JOIN order_items oi ON p.id = oi.product_id
        WHERE p.seller_id = %s
        GROUP BY p.id
        ORDER BY total_sold DESC
        LIMIT 5
    """, (seller_id,), fetch=True)
    
    # Monthly sales (last 6 months)
    monthly_sales = db.execute_query("""
        SELECT DATE_FORMAT(created_at, '%Y-%m') as month, 
               COUNT(*) as orders, 
               SUM(total_amount) as revenue
        FROM orders 
        WHERE seller_id = %s 
          AND created_at >= DATE_SUB(NOW(), INTERVAL 6 MONTH)
        GROUP BY DATE_FORMAT(created_at, '%Y-%m')
        ORDER BY month DESC
    """, (seller_id,), fetch=True)
    
    return render_template('seller/dashboard.html', 
                         seller=seller,
                         product_stats=product_stats,
                         order_stats=order_stats,
                         products=products,
                         orders=recent_orders,
                         top_products=top_products,
                         monthly_sales=monthly_sales)

@seller_bp.route('/products')
@login_required
@seller_required
def products():
    seller_id = session['user_id']
    products = Product.list(seller_id=seller_id, status=None)
    db = Database()
    categories = db.execute_query("SELECT * FROM categories WHERE is_active = 1", fetch=True)
    return render_template('seller/products.html', products=products, categories=categories)

@seller_bp.route('/products/add', methods=['POST'])
@login_required
@seller_required
def add_product():
    seller_id = session['user_id']
    
    # Get categories to populate form choices
    db = Database()
    categories = db.execute_query("SELECT id, name FROM categories WHERE is_active = 1", fetch=True)
    
    form = SellerProductForm()
    form.category_id.choices = [(cat['id'], cat['name']) for cat in categories]
    
    if form.validate_on_submit():
        try:
            Product.create(
                seller_id=seller_id,
                category_id=form.category_id.data,
                name=form.name.data.strip(),
                description=form.description.data.strip() if form.description.data else None,
                price=form.price.data,
                stock_quantity=form.stock_quantity.data,
                image_url=form.image_url.data.strip() if form.image_url.data else None
            )
            flash('Product created successfully!', 'success')
        except Exception as e:
            flash('Failed to create product.', 'error')
    else:
        flash('Please correct the errors in the form.', 'error')
    
    return redirect(url_for('seller.products'))

@seller_bp.route('/products/<int:product_id>/edit', methods=['POST'])
@login_required
@seller_required
def edit_product(product_id):
    seller_id = session['user_id']
    product = Product.get_by_id(product_id)
    if not product or product['seller_id'] != seller_id:
        flash('Product not found or unauthorized.', 'error')
        return redirect(url_for('seller.products'))
    
    # Get categories to populate form choices
    db = Database()
    categories = db.execute_query("SELECT id, name FROM categories WHERE is_active = 1", fetch=True)
    
    form = SellerProductForm()
    form.category_id.choices = [(cat['id'], cat['name']) for cat in categories]
    
    if form.validate_on_submit():
        try:
            Product.update(product_id,
                          name=form.name.data.strip(),
                          category_id=form.category_id.data,
                          description=form.description.data.strip() if form.description.data else None,
                          price=form.price.data,
                          stock_quantity=form.stock_quantity.data,
                          image_url=form.image_url.data.strip() if form.image_url.data else None,
                          status=form.status.data)
            flash('Product updated!', 'success')
        except Exception as e:
            flash('Failed to update product.', 'error')
    else:
        flash('Please correct the errors in the form.', 'error')
    
    return redirect(url_for('seller.products'))

@seller_bp.route('/products/<int:product_id>/delete', methods=['POST'])
@login_required
@seller_required
def delete_product(product_id):
    seller_id = session['user_id']
    product = Product.get_by_id(product_id)
    if not product or product['seller_id'] != seller_id:
        flash('Product not found or unauthorized.', 'error')
        return redirect(url_for('seller.products'))
    try:
        Product.delete(product_id)
        flash('Product deleted.', 'info')
    except Exception as e:
        flash('Failed to delete product.', 'error')
    return redirect(url_for('seller.products'))

@seller_bp.route('/orders')
@login_required
@seller_required
def orders():
    seller_id = session['user_id']
    status = request.args.get('status')
    orders = Order.list_for_seller(seller_id, status=status)
    # Add rider info to orders
    db = Database()
    for order in orders:
        if order['rider_id']:
            rider = db.execute_query(
                "SELECT first_name, last_name, phone FROM users WHERE id = %s",
                (order['rider_id'],),
                fetch=True, fetchone=True
            )
            if rider:
                order['rider_name'] = f"{rider['first_name']} {rider['last_name']}"
                order['rider_phone'] = rider['phone'] or ''
            else:
                order['rider_name'] = 'Unknown Rider'
                order['rider_phone'] = ''
        else:
            order['rider_name'] = None
            order['rider_phone'] = None
    return render_template('seller/orders.html', orders=orders, status=status)

@seller_bp.route('/assign-rider', methods=['POST'])
@login_required
@seller_required
def assign_rider():
    order_id = request.form.get('order_id')
    rider_id = request.form.get('rider_id')
    delivery_notes = request.form.get('delivery_notes', '')
    try:
        # Check if order exists and belongs to seller
        order = Order.get_by_id(order_id)
        if not order or order['seller_id'] != session['user_id']:
            flash('Order not found or unauthorized.', 'error')
            return redirect(url_for('seller.orders'))
        
        # Check if already assigned
        if order['rider_id']:
            flash('Rider already assigned to this order.', 'error')
            return redirect(url_for('seller.orders'))
        
        if Delivery.create(order_id, rider_id, delivery_notes):
            flash('Rider assigned successfully.', 'success')
        else:
            flash('Failed to assign rider. Please try again.', 'error')
    except Exception as e:
        print(f"Error in assign_rider: {e}")
        flash('Error assigning rider. Please contact support.', 'error')
    return redirect(url_for('seller.orders'))

@seller_bp.route('/get-available-riders')
@login_required
@seller_required
def get_available_riders():
    from app.models.delivery import Delivery
    riders = Delivery.get_all_riders_with_availability()
    return jsonify([{
        'id': r['id'], 
        'name': f"{r['first_name']} {r['last_name']}", 
        'phone': r['phone'], 
        'current_deliveries': r['current_deliveries'],
        'is_available': r['current_deliveries'] < 5
    } for r in riders])

@seller_bp.route('/orders/update-status', methods=['POST'])
@login_required
@seller_required
def update_order_status():
    form = OrderStatusForm()
    if form.validate_on_submit():
        order_id = request.form.get('order_id')
        status = form.status.data
        try:
            # Fetch order to get customer info for notification
            order = Order.get_by_id(order_id)
            if not order or order['seller_id'] != session['user_id']:
                flash('Order not found or unauthorized.', 'error')
                return redirect(url_for('seller.orders'))
            
            customer = User.get_by_id(order['user_id'])
            if customer and customer['email']:
                # TODO: Implement actual email notification (e.g., using Flask-Mail)
                print(f"Notification: Order {order_id} status changed to '{status}' for customer {customer['email']}")
            
            # Auto-assign rider if status is 'shipped' and no rider assigned
            if status == 'shipped' and not order['rider_id']:
                all_riders = Delivery.get_all_riders_with_availability()
                available_riders = [r for r in all_riders if r['current_deliveries'] < 5]
                if available_riders:
                    first_rider = available_riders[0]
                    if Delivery.create(order_id, first_rider['id'], 'Auto-assigned on ship'):
                        flash('Order status updated, rider auto-assigned, and customer notified.', 'success')
                    else:
                        flash('Order status updated but failed to auto-assign rider.', 'warning')
                else:
                    flash('No available riders. Please assign manually.', 'warning')
            else:
                Order.update_status(order_id, status)
                flash('Order status updated and customer notified.', 'success')
        except Exception as e:
            print(f"Error in update_order_status: {e}")
            flash('Failed to update order status. Please try again.', 'error')
    else:
        flash('Invalid form data.', 'error')
    
    return redirect(url_for('seller.orders'))


@seller_bp.route('/order/<int:order_id>/details')
@login_required
@seller_required
def order_details(order_id):
    order = Order.get_by_id(order_id)
    if not order or order['seller_id'] != session['user_id']:
        return jsonify({'error': 'Order not found or unauthorized.'}), 404
    
    # Add customer details
    user = User.get_by_id(order['user_id'])
    if user:
        order['customer_name'] = f"{user['first_name']} {user['last_name']}"
        order['customer_email'] = user['email']
        order['customer_phone'] = user['phone'] or ''
    else:
        order['customer_name'] = 'Unknown'
        order['customer_email'] = ''
        order['customer_phone'] = ''
    
    order['items_count'] = len(order['items'])
    
    html = render_template('seller/order_detail_modal.html', order=order)
    return jsonify({'html': html})

# Seller application route (for regular users to become sellers)
@seller_bp.route('/apply', methods=['GET', 'POST'])
@login_required
def apply():
    """Apply to become a seller"""
    user = User.get_by_id(session['user_id'])
    
    # Check if user is already a seller
    if user['role'] == 'seller':
        flash('You are already a seller.', 'info')
        return redirect(url_for('seller.dashboard'))
    
    # Check if user has a pending application
    existing_request = SellerRequest.get_by_user_id(session['user_id'])
    if existing_request and existing_request['status'] == 'pending':
        flash('You already have a pending seller application.', 'info')
        return render_template('seller/application_pending.html', request=existing_request)
    
    form = SellerApplicationForm()
    if form.validate_on_submit():
        try:
            SellerRequest.create(
                user_id=session['user_id'],
                business_name=form.business_name.data.strip(),
                business_description=form.business_description.data.strip(),
                business_address=form.business_address.data.strip(),
                business_phone=form.business_phone.data.strip(),
                tax_id=form.tax_id.data.strip() if form.tax_id.data else None
            )
            flash('Your seller application has been submitted! We will review it and get back to you.', 'success')
            return redirect(url_for('user.dashboard'))
        except Exception as e:
            flash('Failed to submit application. Please try again.', 'error')
    
    return render_template('seller/apply.html', form=form)

@seller_bp.route('/analytics')
@login_required
@seller_required
def analytics():
    """Detailed seller analytics"""
    seller_id = session['user_id']
    db = Database()
    
    # Revenue trends (last 12 months)
    revenue_trends = db.execute_query("""
        SELECT DATE_FORMAT(created_at, '%Y-%m') as month,
               COUNT(*) as orders,
               SUM(total_amount) as revenue,
               AVG(total_amount) as avg_order_value
        FROM orders 
        WHERE seller_id = %s 
          AND created_at >= DATE_SUB(NOW(), INTERVAL 12 MONTH)
        GROUP BY DATE_FORMAT(created_at, '%Y-%m')
        ORDER BY month ASC
    """, (seller_id,), fetch=True)
    
    # Product performance
    product_performance = db.execute_query("""
        SELECT p.name, p.price, p.stock_quantity,
               COUNT(oi.id) as times_ordered,
               SUM(oi.quantity) as total_sold,
               SUM(oi.quantity * oi.price_at_time) as total_revenue,
               AVG(r.rating) as avg_rating,
               COUNT(r.id) as review_count
        FROM products p
        LEFT JOIN order_items oi ON p.id = oi.product_id
        LEFT JOIN reviews r ON p.id = r.product_id
        WHERE p.seller_id = %s
        GROUP BY p.id
        ORDER BY total_revenue DESC
    """, (seller_id,), fetch=True)
    
    # Customer insights
    customer_insights = db.execute_query("""
        SELECT u.first_name, u.last_name, u.email,
               COUNT(o.id) as total_orders,
               SUM(o.total_amount) as total_spent,
               MAX(o.created_at) as last_order_date
        FROM users u
        JOIN orders o ON u.id = o.user_id
        WHERE o.seller_id = %s
        GROUP BY u.id
        ORDER BY total_spent DESC
        LIMIT 20
    """, (seller_id,), fetch=True)
    
    # Order status breakdown
    order_status_breakdown = db.execute_query("""
        SELECT status, COUNT(*) as count
        FROM orders
        WHERE seller_id = %s
        GROUP BY status
    """, (seller_id,), fetch=True)
    
    return render_template('seller/analytics.html',
                         revenue_trends=revenue_trends,
                         product_performance=product_performance,
                         customer_insights=customer_insights,
                         order_status_breakdown=order_status_breakdown)

@seller_bp.route('/inventory')
@login_required
@seller_required
def inventory():
    """Inventory management"""
    seller_id = session['user_id']
    
    # Get products with low stock alert
    low_stock_threshold = 5
    products = Product.list(seller_id=seller_id, status=None)
    
    low_stock_products = [p for p in products if p['stock_quantity'] <= low_stock_threshold]
    out_of_stock_products = [p for p in products if p['stock_quantity'] == 0]
    
    return render_template('seller/inventory.html',
                         products=products,
                         low_stock_products=low_stock_products,
                         out_of_stock_products=out_of_stock_products,
                         low_stock_threshold=low_stock_threshold)

@seller_bp.route('/inventory/update-stock', methods=['POST'])
@login_required
@seller_required
def update_stock():
    """Update product stock quantity"""
    try:
        product_id = int(request.form.get('product_id'))
        new_stock = int(request.form.get('stock_quantity'))
        
        if new_stock < 0:
            flash('Stock quantity cannot be negative.', 'error')
            return redirect(url_for('seller.inventory'))
        
        # Verify product belongs to current seller
        seller_id = session['user_id']
        product = Product.get_by_id(product_id)
        
        if not product or product['seller_id'] != seller_id:
            flash('Product not found or unauthorized.', 'error')
            return redirect(url_for('seller.inventory'))
        
        # Update stock
        Product.update(product_id, stock_quantity=new_stock)
        flash(f'Stock updated for "{product["name"]}"', 'success')
        
    except (ValueError, TypeError):
        flash('Invalid input.', 'error')
    except Exception as e:
        flash('Failed to update stock.', 'error')
    
    return redirect(url_for('seller.inventory'))

@seller_bp.route('/bulk-stock-update', methods=['POST'])
@login_required
@seller_required
def bulk_stock_update():
    """Bulk update stock quantities"""
    seller_id = session['user_id']
    
    try:
        updates = request.get_json()
        if not updates:
            return jsonify({'error': 'No updates provided'}), 400
        
        success_count = 0
        for update in updates:
            product_id = int(update['product_id'])
            new_stock = int(update['stock_quantity'])
            
            # Verify ownership
            product = Product.get_by_id(product_id)
            if product and product['seller_id'] == seller_id and new_stock >= 0:
                Product.update(product_id, stock_quantity=new_stock)
                success_count += 1
        
        return jsonify({
            'success': True,
            'message': f'{success_count} products updated successfully'
        })
        
    except Exception as e:
        return jsonify({'error': 'Failed to update stock quantities'}), 500

@seller_bp.route('/reports')
@login_required
@seller_required
def reports():
    """Sales reports for seller"""
    seller_id = session['user_id']
    db = Database()
    
    # Date range from request
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Default to last 30 days if no range provided
    if not start_date or not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    # Sales summary for the period
    sales_summary = db.execute_query("""
        SELECT 
            COUNT(*) as total_orders,
            SUM(total_amount) as total_revenue,
            AVG(total_amount) as avg_order_value,
            MIN(total_amount) as min_order,
            MAX(total_amount) as max_order
        FROM orders
        WHERE seller_id = %s 
          AND DATE(created_at) BETWEEN %s AND %s
    """, (seller_id, start_date, end_date), fetch=True, fetchone=True)
    
    # Daily sales breakdown
    daily_sales = db.execute_query("""
        SELECT DATE(created_at) as date,
               COUNT(*) as orders,
               SUM(total_amount) as revenue
        FROM orders
        WHERE seller_id = %s 
          AND DATE(created_at) BETWEEN %s AND %s
        GROUP BY DATE(created_at)
        ORDER BY date ASC
    """, (seller_id, start_date, end_date), fetch=True)
    
    # Product sales in period
    product_sales = db.execute_query("""
        SELECT p.name, 
               COUNT(oi.id) as times_ordered,
               SUM(oi.quantity) as quantity_sold,
               SUM(oi.quantity * oi.price_at_time) as revenue
        FROM products p
        JOIN order_items oi ON p.id = oi.product_id
        JOIN orders o ON oi.order_id = o.id
        WHERE p.seller_id = %s 
          AND DATE(o.created_at) BETWEEN %s AND %s
        GROUP BY p.id
        ORDER BY revenue DESC
    """, (seller_id, start_date, end_date), fetch=True)
    
    return render_template('seller/reports.html',
                         sales_summary=sales_summary,
                         daily_sales=daily_sales,
                         product_sales=product_sales,
                         start_date=start_date,
                         end_date=end_date)

