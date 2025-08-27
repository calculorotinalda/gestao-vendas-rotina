from flask import render_template, request, redirect, url_for, flash, jsonify, session
from app import app, db
from models import (User, Category, Supplier, Customer, Product, Sale, SaleItem, 
                   Purchase, PurchaseItem, InventoryMovement, Configuration)
from utils import format_currency, generate_invoice_number, calculate_totals
from sqlalchemy import func, desc, asc
from datetime import datetime, timedelta
import logging

# Initialize default user and configurations when database is available
def initialize_default_data():
    try:
        with app.app_context():
            # Create default admin user if it doesn't exist
            admin_user = User.query.filter_by(username='admin').first()
            if not admin_user:
                admin_user = User(
                    username='admin',
                    email='admin@gestvendas.com',
                    full_name='Administrador',
                    role='admin'
                )
                admin_user.set_password('admin123')
                db.session.add(admin_user)
                
            # Create default configurations
            default_configs = [
                {'key': 'currency', 'value': 'EUR', 'description': 'Moeda padrão do sistema'},
                {'key': 'currency_symbol', 'value': '€', 'description': 'Símbolo da moeda'},
                {'key': 'tax_rate', 'value': '23.00', 'description': 'Taxa de IVA padrão (%)', 'data_type': 'decimal'},
                {'key': 'company_name', 'value': 'GestVendas', 'description': 'Nome da empresa'},
                {'key': 'company_address', 'value': '', 'description': 'Endereço da empresa'},
                {'key': 'company_tax_number', 'value': '', 'description': 'Número fiscal da empresa'},
            ]
            
            for config_data in default_configs:
                existing_config = Configuration.query.filter_by(key=config_data['key']).first()
                if not existing_config:
                    config = Configuration(**config_data)
                    db.session.add(config)
            
            db.session.commit()
            return True
    except Exception as e:
        logging.error(f"Error creating default data: {e}")
        if 'session' in locals():
            db.session.rollback()
        return False

# Helper function to check if user is logged in
def login_required():
    return session.get('user_id') is not None

@app.route('/')
def index():
    if not login_required():
        return redirect(url_for('login'))
    
    # Get dashboard statistics
    today = datetime.utcnow().date()
    month_start = today.replace(day=1)
    
    # Sales statistics
    total_sales = db.session.query(func.sum(Sale.total_amount)).filter(
        Sale.status != 'cancelado'
    ).scalar() or 0
    
    monthly_sales = db.session.query(func.sum(Sale.total_amount)).filter(
        Sale.sale_date >= month_start,
        Sale.status != 'cancelado'
    ).scalar() or 0
    
    # Purchase statistics  
    total_purchases = db.session.query(func.sum(Purchase.total_amount)).filter(
        Purchase.status != 'cancelado'
    ).scalar() or 0
    
    monthly_purchases = db.session.query(func.sum(Purchase.total_amount)).filter(
        Purchase.purchase_date >= month_start,
        Purchase.status != 'cancelado'
    ).scalar() or 0
    
    # Inventory alerts
    low_stock_products = Product.query.filter(
        Product.stock_quantity <= Product.min_stock,
        Product.is_active == True
    ).count()
    
    # Recent sales
    recent_sales = Sale.query.join(Customer).add_columns(
        Customer.name.label('customer_name')
    ).order_by(desc(Sale.created_at)).limit(5).all()
    
    # Products needing restock
    restock_products = Product.query.filter(
        Product.stock_quantity <= Product.min_stock,
        Product.is_active == True
    ).limit(5).all()
    
    stats = {
        'total_sales': total_sales,
        'monthly_sales': monthly_sales,
        'total_purchases': total_purchases,
        'monthly_purchases': monthly_purchases,
        'profit': total_sales - total_purchases,
        'low_stock_alerts': low_stock_products,
        'recent_sales': recent_sales,
        'restock_products': restock_products
    }
    
    return render_template('index.html', stats=stats)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username, is_active=True).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['user_role'] = user.role
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Credenciais inválidas!', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logout realizado com sucesso!', 'success')
    return redirect(url_for('login'))

# Products routes
@app.route('/products')
def products():
    if not login_required():
        return redirect(url_for('login'))
    
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    category_id = request.args.get('category', type=int)
    
    query = Product.query.join(Category).join(Supplier, isouter=True)
    
    if search:
        query = query.filter(Product.name.contains(search) | Product.code.contains(search))
    
    if category_id:
        query = query.filter(Product.category_id == category_id)
    
    products = query.order_by(Product.name).paginate(
        page=page, per_page=20, error_out=False
    )
    
    categories = Category.query.filter_by(is_active=True).all()
    
    return render_template('products.html', products=products, categories=categories, 
                         search=search, selected_category=category_id)

@app.route('/products/add', methods=['GET', 'POST'])
def add_product():
    if not login_required():
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            product = Product(
                code=request.form['code'],
                name=request.form['name'],
                description=request.form.get('description', ''),
                category_id=request.form['category_id'],
                supplier_id=request.form.get('supplier_id') or None,
                unit=request.form.get('unit', 'unidade'),
                purchase_price=float(request.form.get('purchase_price', 0)),
                sale_price=float(request.form['sale_price']),
                stock_quantity=int(request.form.get('stock_quantity', 0)),
                min_stock=int(request.form.get('min_stock', 5)),
                max_stock=int(request.form.get('max_stock', 100)),
                tax_rate=float(request.form.get('tax_rate', 23.00))
            )
            
            db.session.add(product)
            db.session.commit()
            
            flash('Produto adicionado com sucesso!', 'success')
            return redirect(url_for('products'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao adicionar produto: {str(e)}', 'error')
    
    categories = Category.query.filter_by(is_active=True).all()
    suppliers = Supplier.query.filter_by(is_active=True).all()
    
    return render_template('product_form.html', categories=categories, suppliers=suppliers)

# Sales routes
@app.route('/sales')
def sales():
    if not login_required():
        return redirect(url_for('login'))
    
    page = request.args.get('page', 1, type=int)
    sales = Sale.query.join(Customer).add_columns(
        Customer.name.label('customer_name')
    ).order_by(desc(Sale.created_at)).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('sales.html', sales=sales)

@app.route('/sales/add', methods=['GET', 'POST'])
def add_sale():
    if not login_required():
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            # Create sale
            sale = Sale(
                invoice_number=generate_invoice_number('V'),
                customer_id=request.form['customer_id'],
                user_id=session['user_id'],
                sale_date=datetime.strptime(request.form['sale_date'], '%Y-%m-%d'),
                payment_method=request.form.get('payment_method'),
                notes=request.form.get('notes', '')
            )
            
            db.session.add(sale)
            db.session.flush()  # Get the sale ID
            
            # Add sale items
            products_data = request.form.getlist('products')
            quantities = request.form.getlist('quantities')
            unit_prices = request.form.getlist('unit_prices')
            
            subtotal = 0
            tax_total = 0
            
            for i, product_id in enumerate(products_data):
                if product_id and quantities[i] and unit_prices[i]:
                    product = Product.query.get(product_id)
                    quantity = int(quantities[i])
                    unit_price = float(unit_prices[i])
                    total_price = quantity * unit_price
                    tax_amount = total_price * (product.tax_rate / 100)
                    
                    sale_item = SaleItem(
                        sale_id=sale.id,
                        product_id=product_id,
                        quantity=quantity,
                        unit_price=unit_price,
                        tax_rate=product.tax_rate,
                        total_price=total_price
                    )
                    
                    db.session.add(sale_item)
                    
                    # Update stock
                    product.stock_quantity -= quantity
                    
                    # Create inventory movement
                    movement = InventoryMovement(
                        product_id=product_id,
                        movement_type='saida',
                        quantity=quantity,
                        reference_type='venda',
                        reference_id=sale.id,
                        user_id=session['user_id']
                    )
                    db.session.add(movement)
                    
                    subtotal += total_price
                    tax_total += tax_amount
            
            # Update sale totals
            sale.subtotal = subtotal
            sale.tax_amount = tax_total
            sale.total_amount = subtotal + tax_total
            
            db.session.commit()
            flash('Venda registrada com sucesso!', 'success')
            return redirect(url_for('sales'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao registrar venda: {str(e)}', 'error')
    
    customers = Customer.query.filter_by(is_active=True).all()
    products = Product.query.filter_by(is_active=True).all()
    
    return render_template('sale_form.html', customers=customers, products=products)

# Customers routes
@app.route('/customers')
def customers():
    if not login_required():
        return redirect(url_for('login'))
    
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = Customer.query
    if search:
        query = query.filter(Customer.name.contains(search) | Customer.email.contains(search))
    
    customers = query.order_by(Customer.name).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('customers.html', customers=customers, search=search)

@app.route('/customers/add', methods=['GET', 'POST'])
def add_customer():
    if not login_required():
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            customer = Customer(
                name=request.form['name'],
                email=request.form.get('email', ''),
                phone=request.form.get('phone', ''),
                address=request.form.get('address', ''),
                city=request.form.get('city', ''),
                postal_code=request.form.get('postal_code', ''),
                country=request.form.get('country', 'Portugal'),
                tax_number=request.form.get('tax_number', ''),
                customer_type=request.form.get('customer_type', 'particular')
            )
            
            db.session.add(customer)
            db.session.commit()
            
            flash('Cliente adicionado com sucesso!', 'success')
            return redirect(url_for('customers'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao adicionar cliente: {str(e)}', 'error')
    
    return render_template('customer_form.html')

# API routes for AJAX requests
@app.route('/api/products/search')
def api_search_products():
    if not login_required():
        return jsonify({'error': 'Unauthorized'}), 401
    
    query = request.args.get('q', '')
    products = Product.query.filter(
        Product.name.contains(query) | Product.code.contains(query),
        Product.is_active == True
    ).limit(10).all()
    
    result = []
    for product in products:
        result.append({
            'id': product.id,
            'code': product.code,
            'name': product.name,
            'sale_price': float(product.sale_price),
            'stock_quantity': product.stock_quantity,
            'unit': product.unit
        })
    
    return jsonify(result)

@app.route('/api/dashboard/charts')
def api_dashboard_charts():
    if not login_required():
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Get sales data for the last 12 months
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=365)
    
    monthly_sales = db.session.query(
        func.date_trunc('month', Sale.sale_date).label('month'),
        func.sum(Sale.total_amount).label('total')
    ).filter(
        Sale.sale_date >= start_date,
        Sale.status != 'cancelado'
    ).group_by('month').order_by('month').all()
    
    sales_data = {
        'labels': [sale.month.strftime('%b %Y') for sale in monthly_sales],
        'data': [float(sale.total) for sale in monthly_sales]
    }
    
    # Get top products by sales
    top_products = db.session.query(
        Product.name,
        func.sum(SaleItem.quantity).label('quantity_sold'),
        func.sum(SaleItem.total_price).label('revenue')
    ).join(SaleItem).join(Sale).filter(
        Sale.status != 'cancelado'
    ).group_by(Product.id, Product.name).order_by(
        desc('revenue')
    ).limit(5).all()
    
    products_data = {
        'labels': [product.name for product in top_products],
        'quantities': [int(product.quantity_sold) for product in top_products],
        'revenues': [float(product.revenue) for product in top_products]
    }
    
    return jsonify({
        'sales': sales_data,
        'products': products_data
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', 
                         error_code=404,
                         error_message='Página não encontrada'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('error.html',
                         error_code=500,
                         error_message='Erro interno do servidor'), 500

# Context processors
@app.context_processor
def inject_utils():
    return {
        'format_currency': format_currency,
        'current_user_id': session.get('user_id'),
        'current_username': session.get('username'),
        'current_user_role': session.get('user_role')
    }

# Analytics route
@app.route('/analytics')
def analytics():
    if not login_required():
        return redirect(url_for('login'))
    
    try:
        from models import Sale, Product, Purchase, Customer, SaleItem, PurchaseItem, Category
        from datetime import datetime, timedelta
        from sqlalchemy import func
        
        # Calculate analytics data
        now = datetime.now()
        last_30_days = now - timedelta(days=30)
        last_60_days = now - timedelta(days=60)
        
        # Revenue growth calculation
        current_revenue = db.session.query(func.sum(Sale.total_amount)).filter(
            Sale.created_at >= last_30_days
        ).scalar() or 0
        
        previous_revenue = db.session.query(func.sum(Sale.total_amount)).filter(
            Sale.created_at >= last_60_days,
            Sale.created_at < last_30_days
        ).scalar() or 0
        
        revenue_growth = ((current_revenue - previous_revenue) / previous_revenue * 100) if previous_revenue > 0 else 0
        
        # Average order value
        recent_sales = Sale.query.filter(Sale.created_at >= last_30_days).all()
        avg_order_value = (sum(sale.total_amount for sale in recent_sales) / len(recent_sales)) if recent_sales else 0
        
        # Profit margin calculation
        total_revenue = sum(sale.total_amount for sale in recent_sales)
        total_purchase_costs = db.session.query(func.sum(Purchase.total_amount)).filter(
            Purchase.created_at >= last_30_days
        ).scalar() or 0
        
        profit_margin = ((total_revenue - total_purchase_costs) / total_revenue * 100) if total_revenue > 0 else 0
        
        # Inventory turnover (simplified)
        total_products = Product.query.count()
        sold_products = db.session.query(func.sum(SaleItem.quantity)).join(Sale).filter(
            Sale.created_at >= last_30_days
        ).scalar() or 0
        inventory_turnover = (sold_products / total_products * 12) if total_products > 0 else 0
        
        # Revenue vs Purchase data for chart (last 7 days)
        revenue_labels = []
        revenue_data = []
        purchase_data = []
        
        for i in range(7):
            date = now - timedelta(days=6-i)
            day_label = date.strftime('%d/%m')
            revenue_labels.append(day_label)
            
            day_revenue = db.session.query(func.sum(Sale.total_amount)).filter(
                func.date(Sale.created_at) == date.date()
            ).scalar() or 0
            revenue_data.append(float(day_revenue))
            
            day_purchases = db.session.query(func.sum(Purchase.total_amount)).filter(
                func.date(Purchase.created_at) == date.date()
            ).scalar() or 0
            purchase_data.append(float(day_purchases))
        
        # Category sales distribution
        category_sales = db.session.query(
            Category.name,
            func.sum(SaleItem.total_price)
        ).join(Product).join(SaleItem).join(Sale).filter(
            Sale.created_at >= last_30_days
        ).group_by(Category.name).all()
        
        category_labels = [item[0] for item in category_sales]
        category_data = [float(item[1]) for item in category_sales]
        
        # Top products by sales
        top_products = db.session.query(
            Product.name,
            func.sum(SaleItem.total_price)
        ).join(SaleItem).join(Sale).filter(
            Sale.created_at >= last_30_days
        ).group_by(Product.name).order_by(
            func.sum(SaleItem.total_price).desc()
        ).limit(5).all()
        
        top_products_labels = [item[0] for item in top_products]
        top_products_data = [float(item[1]) for item in top_products]
        
        # Margin analysis (volume vs margin)
        margin_analysis = []
        for product in Product.query.all():
            volume = db.session.query(func.sum(SaleItem.quantity)).filter(
                SaleItem.product_id == product.id
            ).scalar() or 0
            margin = product.profit_margin
            if volume > 0:
                margin_analysis.append({'x': volume, 'y': margin})
        
        # Top customers
        top_customers = db.session.query(
            Customer.name,
            func.count(Sale.id).label('sales_count'),
            func.sum(Sale.total_amount).label('total_amount')
        ).join(Sale).filter(
            Sale.created_at >= last_30_days
        ).group_by(Customer.id, Customer.name).order_by(
            func.sum(Sale.total_amount).desc()
        ).limit(5).all()
        
        # Stock alerts
        stock_alerts = Product.query.filter(
            Product.stock_quantity <= Product.min_stock
        ).all()
        
        # Financial totals
        total_costs = float(total_purchase_costs)
        gross_profit = float(total_revenue - total_costs)
        roi = (gross_profit / total_costs * 100) if total_costs > 0 else 0
        
        analytics_data = {
            'revenue_growth': round(revenue_growth, 1),
            'profit_margin': round(profit_margin, 1),
            'avg_order_value': float(avg_order_value),
            'inventory_turnover': round(inventory_turnover, 1),
            'revenue_labels': revenue_labels,
            'revenue_data': revenue_data,
            'purchase_data': purchase_data,
            'category_labels': category_labels,
            'category_data': category_data,
            'top_products_labels': top_products_labels,
            'top_products_data': top_products_data,
            'margin_analysis': margin_analysis,
            'top_customers': [{'name': c[0], 'sales_count': c[1], 'total_amount': float(c[2])} for c in top_customers],
            'stock_alerts': stock_alerts,
            'total_revenue': float(total_revenue),
            'total_costs': total_costs,
            'gross_profit': gross_profit,
            'roi': round(roi, 1)
        }
        
        return render_template('analytics.html', analytics=analytics_data)
        
    except Exception as e:
        print(f"Error in analytics: {e}")
        flash('Erro ao carregar análises.', 'error')
        return redirect(url_for('dashboard'))
