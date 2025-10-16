# Pawfect Finds - The Purrfect Shop 🐾

A comprehensive e-commerce platform for pet supplies built with Flask, featuring multi-role functionality for customers, sellers, admins, and delivery riders.

## Features

### 🛍️ Customer Features
- Browse and search products by category, pet type, price range
- Shopping cart and secure checkout
- Order tracking and history
- Product reviews and ratings
- Wishlist functionality
- User profile management
- Request to become a seller

### 🏪 Seller Features
- Comprehensive seller dashboard with analytics
- Product management (CRUD operations)
- Inventory tracking and low stock alerts
- Order management and status updates
- Sales analytics and reporting
- Profile and business information management

### 👨‍💼 Admin Features
- Approve/reject seller applications
- User management (customers, sellers, riders)
- System monitoring and analytics
- Content moderation (reviews, products)
- Website settings management

### 🚴 Rider Features
- View assigned delivery orders
- Update delivery status (on the way, delivered, cancelled)
- Earnings tracking and payment history
- Performance ratings from sellers
- Profile management

## Tech Stack

- **Backend**: Python Flask
- **Database**: MySQL with XAMPP
- **Frontend**: HTML5, CSS3, Bootstrap 5, JavaScript
- **Authentication**: Flask-WTF with session management
- **File Handling**: Werkzeug for image uploads

## Installation & Setup

### Prerequisites
- Python 3.8 or higher
- XAMPP (for MySQL database)
- Git

### 1. Clone the Repository
```bash
git clone <repository-url>
cd pawfect-finds
```

### 2. Create Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Database Setup

#### Start XAMPP and MySQL
1. Start XAMPP Control Panel
2. Start Apache and MySQL services
3. Open phpMyAdmin (http://localhost/phpmyadmin)

#### Create Database
1. Create a new database named `petsupplies_db`
2. Import the database schema:
   - Navigate to the database
   - Import `database/schema.sql`

Or run the SQL commands directly:
```sql
-- Run the contents of database/schema.sql
```

### 5. Environment Configuration (Optional)
Create a `.env` file in the root directory:
```env
FLASK_CONFIG=development
SECRET_KEY=your-secret-key-here
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=your-mysql-password
MYSQL_DB=petsupplies_db
```

### 6. Initialize Database and Create Sample Data
```bash
# Initialize database tables and create admin user
flask init-db

# Create sample data for testing
flask create-sample-data
```

### 7. Run the Application
```bash
python run.py
```

The application will be available at `http://localhost:5000`

## Default Accounts

After running the setup commands, you can use these test accounts:

- **Admin**: admin@pawfectfinds.com / admin123
- **Seller**: seller@test.com / password123  
- **Customer**: customer@test.com / password123

## Project Structure

```
pawfect-finds/
│
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── models/
│   │   └── models.py            # Database models
│   ├── routes/
│   │   ├── auth.py              # Authentication routes
│   │   ├── main.py              # Public pages routes
│   │   ├── customer.py          # Customer functionality
│   │   ├── seller.py            # Seller functionality
│   │   ├── admin.py             # Admin functionality (to be implemented)
│   │   └── rider.py             # Rider functionality (to be implemented)
│   ├── templates/
│   │   ├── base.html            # Base template
│   │   ├── auth/                # Authentication templates
│   │   ├── public/              # Public page templates
│   │   ├── customer/            # Customer templates (to be implemented)
│   │   ├── seller/              # Seller templates (to be implemented)
│   │   ├── admin/               # Admin templates (to be implemented)
│   │   └── rider/               # Rider templates (to be implemented)
│   ├── static/
│   │   ├── css/                 # Stylesheets
│   │   ├── js/                  # JavaScript files
│   │   ├── img/                 # Static images
│   │   └── uploads/             # User uploaded files
│   └── utils/
│       └── auth.py              # Authentication utilities
├── config/
│   └── config.py                # Application configuration
├── database/
│   └── schema.sql               # Database schema
├── requirements.txt             # Python dependencies
├── run.py                       # Application entry point
└── README.md                    # This file
```

## Database Schema

The application uses a comprehensive database schema with the following main tables:

- **users**: Multi-role user management
- **categories**: Product categories
- **products**: Product catalog
- **product_images**: Product image management
- **cart**: Shopping cart items
- **orders**: Order management
- **order_items**: Individual order items
- **reviews**: Product reviews and ratings
- **seller_applications**: Seller registration requests
- **notifications**: System notifications
- **rider_performance**: Delivery performance tracking
- **rider_earnings**: Rider payment management
- **wishlist**: Customer wishlists
- **website_settings**: Configurable site settings

## API Endpoints

### Authentication
- `POST /auth/login` - User login
- `POST /auth/register` - User registration
- `GET /auth/logout` - User logout
- `POST /auth/become-seller` - Request seller status

### Customer
- `GET /customer/dashboard` - Customer dashboard
- `GET /customer/cart` - Shopping cart
- `POST /customer/add-to-cart` - Add item to cart
- `POST /customer/place-order` - Place an order
- `GET /customer/orders` - Order history

### Seller
- `GET /seller/dashboard` - Seller dashboard
- `GET /seller/products` - Manage products
- `POST /seller/product/add` - Add new product
- `PUT /seller/product/edit/<id>` - Edit product
- `GET /seller/orders` - View orders

### Public
- `GET /` - Landing page
- `GET /products` - Product catalog
- `GET /product/<id>` - Product details
- `GET /category/<id>` - Category products

## Contributing

This is a demo project created for educational purposes. The frontend templates are basic and designed to be replaced with a more sophisticated UI by a frontend developer.

## Current Status

✅ **Completed:**
- Database schema and models
- Authentication system with multi-role support
- Customer functionality (shopping, cart, orders, reviews)
- Seller functionality (product management, order processing)
- Basic responsive UI with Bootstrap
- Landing page and public pages

🚧 **To Do:**
- Admin dashboard and functionality
- Rider dashboard and delivery management
- Enhanced notification system
- More comprehensive templates
- Payment gateway integration
- Email notifications
- Advanced analytics and reporting

## License

This project is for educational purposes. Feel free to use and modify as needed.

---

**Happy coding! 🚀**