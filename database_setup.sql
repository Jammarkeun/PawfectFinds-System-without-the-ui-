-- Create database
CREATE DATABASE IF NOT EXISTS pawfect_findsdatabase CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE pawfect_findsdatabase;

-- ====================================================
-- DROP TABLES (if you need to recreate)
-- ====================================================
-- Uncomment these if you need to reset the database
-- DROP TABLE IF EXISTS reviews;
-- DROP TABLE IF EXISTS order_items;
-- DROP TABLE IF EXISTS orders;
-- DROP TABLE IF EXISTS cart;
-- DROP TABLE IF EXISTS products;
-- DROP TABLE IF EXISTS seller_requests;
-- DROP TABLE IF EXISTS categories;
-- DROP TABLE IF EXISTS users;

-- ====================================================
-- USERS TABLE
-- ====================================================
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    phone VARCHAR(20) NULL,
    address TEXT NULL,
    role ENUM('user', 'seller', 'admin', 'rider') DEFAULT 'user',
    status ENUM('active', 'inactive', 'banned') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_role (role),
    INDEX idx_status (status),
    INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ====================================================
-- CATEGORIES TABLE
-- ====================================================
CREATE TABLE IF NOT EXISTS categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT NULL,
    image_url VARCHAR(255) NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_active (is_active),
    INDEX idx_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ====================================================
-- SELLER REQUESTS TABLE
-- ====================================================
CREATE TABLE IF NOT EXISTS seller_requests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    business_name VARCHAR(100) NOT NULL,
    business_description TEXT NULL,
    business_address TEXT NOT NULL,
    business_phone VARCHAR(20) NOT NULL,
    tax_id VARCHAR(50) NULL,
    status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
    admin_notes TEXT NULL,
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMP NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_status (status),
    INDEX idx_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ====================================================
-- PRODUCTS TABLE
-- ====================================================
CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    seller_id INT NOT NULL,
    category_id INT NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT NULL,
    price DECIMAL(10,2) NOT NULL,
    stock_quantity INT DEFAULT 0,
    image_url VARCHAR(255) NULL,
    status ENUM('active', 'inactive', 'out_of_stock') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (seller_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE RESTRICT,
    INDEX idx_seller (seller_id),
    INDEX idx_category (category_id),
    INDEX idx_status (status),
    INDEX idx_name (name),
    INDEX idx_price (price),
    FULLTEXT idx_search (name, description)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ====================================================
-- CART TABLE
-- ====================================================
CREATE TABLE IF NOT EXISTS cart (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_product (user_id, product_id),
    INDEX idx_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ====================================================
-- ORDERS TABLE
-- ====================================================
CREATE TABLE IF NOT EXISTS orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    seller_id INT NOT NULL,
    rider_id INT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    status ENUM('pending', 'confirmed', 'preparing', 'shipped', 'assigned_to_rider', 'picked_up', 'on_the_way', 'delivered', 'cancelled') DEFAULT 'pending',
    shipping_address TEXT NOT NULL,
    payment_method ENUM('cod', 'online') DEFAULT 'cod',
    payment_status ENUM('pending', 'paid', 'refunded') DEFAULT 'pending',
    notes TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT,
    FOREIGN KEY (seller_id) REFERENCES users(id) ON DELETE RESTRICT,
    FOREIGN KEY (rider_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_user (user_id),
    INDEX idx_seller (seller_id),
    INDEX idx_rider (rider_id),
    INDEX idx_status (status),
    INDEX idx_payment (payment_status),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ====================================================
-- DELIVERIES TABLE (for rider assignments and tracking)
-- ====================================================
CREATE TABLE IF NOT EXISTS deliveries (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    rider_id INT NOT NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    picked_up_at TIMESTAMP NULL,
    delivered_at TIMESTAMP NULL,
    delivery_notes TEXT NULL,
    status ENUM('assigned', 'picked_up', 'in_transit', 'delivered', 'failed') DEFAULT 'assigned',
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (rider_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_order_rider (order_id, rider_id),
    INDEX idx_rider (rider_id),
    INDEX idx_status (status),
    INDEX idx_assigned (assigned_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ====================================================
-- ORDER ITEMS TABLE
-- ====================================================
CREATE TABLE IF NOT EXISTS order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    price_at_time DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE RESTRICT,
    INDEX idx_order (order_id),
    INDEX idx_product (product_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ====================================================
-- REVIEWS TABLE
-- ====================================================
CREATE TABLE IF NOT EXISTS reviews (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    product_id INT NOT NULL,
    rating INT NOT NULL CHECK (rating >= 1 AND rating <= 5),
    comment TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_product_review (user_id, product_id),
    INDEX idx_product (product_id),
    INDEX idx_rating (rating)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ====================================================
-- INSERT DEFAULT DATA
-- ====================================================

-- Insert default categories
INSERT INTO categories (name, description, image_url) VALUES
('Dog Food & Treats', 'Premium dog food, treats, and nutritional supplements for all dog breeds and ages', NULL),
('Cat Litter & Accessories', 'Cat litter, litter boxes, toys, scratching posts, and feline accessories', NULL),
('Aquariums & Fish Supplies', 'Fish tanks, filters, pumps, decorations, and aquarium maintenance supplies', NULL),
('Bird Feeders & Food', 'Bird cages, feeders, perches, toys, and specialized bird food', NULL),
('Pet Grooming Products', 'Shampoos, brushes, nail clippers, grooming tools, and spa products', NULL),
('Pet Health & Wellness', 'Vitamins, supplements, first aid supplies, and health monitoring products', NULL);

-- Insert default admin user (password: admin123)
INSERT INTO users (username, email, password_hash, first_name, last_name, phone, address, role) VALUES
('admin', 'admin@pawfectfinds.com', 'pbkdf2:sha256:260000$EPldXnXRcXdYhNUt$6831a3a1a46e6595478cf13fa05d85cd7fe3849ff25d1719f83cbbde066d0412', 'Admin', 'User', '1234567890', '123 Admin Street, Admin City, AC 12345', 'admin');

-- Insert sample seller users (password: seller123)
INSERT INTO users (username, email, password_hash, first_name, last_name, phone, address, role) VALUES
('petstore1', 'seller1@petstore.com', 'pbkdf2:sha256:260000$KnEmmkNgxtEkRu7l$49fa90c5d97e8612334c7318d3587f3b182d9df0075f3b965d65a6f3c5ce5fa8', 'John', 'Smith', '5551234567', '456 Pet Avenue, Pet City, PC 67890', 'seller'),
('happypaws', 'seller2@happypaws.com', 'pbkdf2:sha256:260000$KnEmmkNgxtEkRu7l$49fa90c5d97e8612334c7318d3587f3b182d9df0075f3b965d65a6f3c5ce5fa8', 'Sarah', 'Johnson', '5559876543', '789 Happy Lane, Paw Town, PT 13579', 'seller');

-- Insert sample rider users (password: rider123)
INSERT INTO users (username, email, password_hash, first_name, last_name, phone, address, role) VALUES
('rider1', 'rider1@delivery.com', 'pbkdf2:sha256:260000$YSgQh7tIWyOYTKvz$ca05767ef5ae8c616d10f3302ad29cf2afbe83f848d5c3c878b263382c8b9dc3', 'Alex', 'Rider', '5551112223', '123 Delivery HQ, Rider City, RC 11223', 'rider'),
('rider2', 'rider2@delivery.com', 'pbkdf2:sha256:260000$YSgQh7tIWyOYTKvz$ca05767ef5ae8c616d10f3302ad29cf2afbe83f848d5c3c878b263382c8b9dc3', 'Jordan', 'Swift', '5553334445', '456 Fast Lane, Speed Town, ST 33445', 'rider');

-- Insert sample customer users (password: customer123)
INSERT INTO users (username, email, password_hash, first_name, last_name, phone, address, role) VALUES
('petlover1', 'customer1@example.com', 'pbkdf2:sha256:260000$18tvDaa7LzYBXBGi$d17817193edf01a10b34cec8cdff09ae73cc448fcafab65545e188a0d59c121e', 'Mike', 'Davis', '5552468135', '321 Customer Road, Client City, CC 24680', 'user'),
('doglover', 'customer2@example.com', 'pbkdf2:sha256:260000$18tvDaa7LzYBXBGi$d17817193edf01a10b34cec8cdff09ae73cc448fcafab65545e188a0d59c121e', 'Emily', 'Wilson', '5558642097', '654 Dog Street, Puppy Town, PT 97531', 'user');

-- Insert sample products
INSERT INTO products (seller_id, category_id, name, description, price, stock_quantity, image_url) VALUES
-- Dog products (seller 2 - John Smith)
(2, 1, 'Premium Dry Dog Food - Adult Formula', 'High-quality protein-rich dry food for adult dogs. Made with real chicken and wholesome grains. Supports healthy digestion and shiny coat.', 45.99, 50, 'https://images.unsplash.com/photo-1589941013453-ec89f33b5e95?w=300'),
(2, 1, 'Natural Dog Treats - Chicken Jerky', 'All-natural chicken jerky treats made without artificial preservatives. Perfect for training and rewarding good behavior.', 18.99, 30, 'https://images.unsplash.com/photo-1583337130417-3346a1be7dee?w=300'),
(2, 5, 'Dog Grooming Kit - Complete Set', 'Professional grooming kit including brush, nail clippers, shampoo, and ear cleaner. Everything you need for at-home grooming.', 34.99, 20, 'https://images.unsplash.com/photo-1601758228041-f3b2795255f1?w=300'),

-- Cat products (seller 3 - Sarah Johnson)
(3, 2, 'Clumping Cat Litter - Unscented', 'Premium clumping clay litter with excellent odor control. Dust-free formula that\'s gentle on paws.', 22.99, 40, 'https://images.unsplash.com/photo-1574144611937-0df059b5ef3e?w=300'),
(3, 2, 'Interactive Cat Toy - Feather Wand', 'Engaging feather wand toy that stimulates your cat\'s natural hunting instincts. Promotes exercise and mental stimulation.', 12.99, 25, 'https://images.unsplash.com/photo-1545249390-6bdfa286032f?w=300'),
(3, 6, 'Cat Vitamin Supplement - Hairball Control', 'Natural supplement to reduce hairballs and support digestive health. Made with omega fatty acids and natural fibers.', 19.99, 35, 'https://images.unsplash.com/photo-1571566882372-1598d88abd90?w=300'),

-- Fish products (seller 2 - John Smith)
(2, 3, '10 Gallon Aquarium Starter Kit', 'Complete aquarium kit perfect for beginners. Includes tank, filter, heater, LED lighting, and water conditioner.', 89.99, 15, 'https://images.unsplash.com/photo-1520637836862-4d197d17c35a?w=300'),
(2, 3, 'Tropical Fish Food Flakes', 'Nutritious flake food suitable for all tropical fish. Enhances colors and supports healthy growth.', 8.99, 60, 'https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=300'),

-- Bird products (seller 3 - Sarah Johnson)
(3, 4, 'Large Bird Cage with Perches', 'Spacious cage suitable for medium to large birds. Includes multiple perches, feeding cups, and easy-clean bottom tray.', 129.99, 10, 'https://images.unsplash.com/photo-1552728089-57bdde30beb3?w=300'),
(3, 4, 'Premium Wild Bird Seed Mix', 'High-quality seed mix attracts a variety of wild birds. Contains sunflower seeds, millet, and cracked corn.', 16.99, 45, 'https://images.unsplash.com/photo-1548550023-2bdb3c5beed7?w=300'),

-- Health & wellness products (both sellers)
(2, 6, 'Pet First Aid Kit', 'Comprehensive first aid kit for pets. Includes bandages, antiseptic wipes, thermometer, and emergency guide.', 28.99, 25, 'https://images.unsplash.com/photo-1576201836106-db1758fd1c97?w=300'),
(3, 6, 'Multivitamin Chews for Dogs', 'Daily multivitamin chews that support overall health, immune system, and joint function. Bacon flavored for easy administration.', 24.99, 30, 'https://images.unsplash.com/photo-1587300003388-59208cc962cb?w=300');

-- Insert sample reviews
INSERT INTO reviews (user_id, product_id, rating, comment) VALUES
(4, 1, 5, 'My dog absolutely loves this food! Great quality and he has more energy now.'),
(5, 1, 4, 'Good quality dog food. My picky eater actually finishes his bowl now.'),
(4, 2, 5, 'Perfect training treats. My dog goes crazy for these!'),
(5, 4, 4, 'Great litter with excellent odor control. Would recommend.'),
(4, 7, 5, 'Perfect starter kit for my first aquarium. Everything I needed was included.'),
(5, 9, 5, 'Beautiful cage and very spacious. My parrot loves it!');

-- Insert sample cart items (for testing)
INSERT INTO cart (user_id, product_id, quantity) VALUES
(4, 1, 1),
(4, 5, 2),
(5, 2, 3),
(5, 6, 1);

-- Insert sample orders
INSERT INTO orders (user_id, seller_id, total_amount, status, shipping_address, payment_method, payment_status, notes) VALUES
(4, 2, 45.99, 'delivered', '321 Customer Road, Client City, CC 24680', 'cod', 'paid', 'Leave at front door if not home'),
(5, 3, 35.98, 'shipped', '654 Dog Street, Puppy Town, PT 97531', 'online', 'paid', 'Please handle with care'),
(4, 3, 22.99, 'preparing', '321 Customer Road, Client City, CC 24680', 'cod', 'pending', NULL);

-- Insert sample order items
INSERT INTO order_items (order_id, product_id, quantity, price_at_time) VALUES
(1, 1, 1, 45.99),
(2, 5, 2, 12.99),
(2, 6, 1, 9.99),
(3, 4, 1, 22.99);

-- Insert sample deliveries (for testing)
INSERT INTO deliveries (order_id, rider_id, status) VALUES
(1, 6, 'delivered'),  -- Order 1 assigned to rider1, delivered
(2, 7, 'in_transit'); -- Order 2 assigned to rider2, in transit

-- ====================================================
-- VIEWS FOR ANALYTICS (OPTIONAL)
-- ====================================================

-- View for sales analytics
CREATE OR REPLACE VIEW sales_summary AS
SELECT 
    DATE(o.created_at) as order_date,
    COUNT(o.id) as total_orders,
    SUM(o.total_amount) as total_revenue,
    AVG(o.total_amount) as avg_order_value
FROM orders o
WHERE o.status != 'cancelled'
GROUP BY DATE(o.created_at)
ORDER BY order_date DESC;

-- View for product performance
CREATE OR REPLACE VIEW product_performance AS
SELECT 
    p.id,
    p.name,
    p.price,
    p.stock_quantity,
    COALESCE(SUM(oi.quantity), 0) as total_sold,
    COALESCE(SUM(oi.quantity * oi.price_at_time), 0) as total_revenue,
    COALESCE(AVG(r.rating), 0) as avg_rating,
    COUNT(r.id) as review_count
FROM products p
LEFT JOIN order_items oi ON p.id = oi.product_id
LEFT JOIN orders o ON oi.order_id = o.id AND o.status != 'cancelled'
LEFT JOIN reviews r ON p.id = r.product_id
GROUP BY p.id, p.name, p.price, p.stock_quantity
ORDER BY total_sold DESC;

-- ====================================================
-- INDEXES FOR PERFORMANCE
-- ====================================================

-- Additional indexes for better performance
CREATE INDEX idx_orders_date ON orders(created_at);
CREATE INDEX idx_products_price_range ON products(price, status);
CREATE INDEX idx_reviews_product_rating ON reviews(product_id, rating);

-- ====================================================
-- PROCEDURES FOR COMMON OPERATIONS (OPTIONAL)
-- ====================================================

DELIMITER //

-- Procedure to get user's cart total
CREATE PROCEDURE GetCartTotal(IN user_id INT, OUT cart_total DECIMAL(10,2))
BEGIN
    SELECT COALESCE(SUM(p.price * c.quantity), 0) INTO cart_total
    FROM cart c
    JOIN products p ON c.product_id = p.id
    WHERE c.user_id = user_id;
END //

-- Procedure to update product stock after order
CREATE PROCEDURE UpdateProductStock(IN product_id INT, IN quantity_sold INT)
BEGIN
    UPDATE products 
    SET stock_quantity = stock_quantity - quantity_sold,
        status = CASE 
            WHEN (stock_quantity - quantity_sold) <= 0 THEN 'out_of_stock'
            ELSE status
        END
    WHERE id = product_id;
END //

DELIMITER ;

-- ====================================================
-- COMPLETION MESSAGE
-- ====================================================

SELECT 'Database setup completed successfully!' as Status,
       (SELECT COUNT(*) FROM users) as total_users,
       (SELECT COUNT(*) FROM categories) as total_categories,
       (SELECT COUNT(*) FROM products) as total_products,
       (SELECT COUNT(*) FROM orders) as total_orders;

-- ====================================================
-- DEFAULT CREDENTIALS
-- ====================================================
-- Admin: admin@pawfectfinds.com / admin123
-- Seller 1: seller1@petstore.com / seller123  
-- Seller 2: seller2@happypaws.com / seller123
-- Rider 1: rider1@delivery.com / rider123
-- Rider 2: rider2@delivery.com / rider123
-- Customer 1: customer1@example.com / customer123
-- Customer 2: customer2@example.com / customer123
-- ====================================================