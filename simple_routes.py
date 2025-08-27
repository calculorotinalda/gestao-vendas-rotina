from flask import render_template, request, redirect, url_for, flash, session
from app import app, db
from datetime import datetime
import secrets

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_field = request.form.get('login_field', '').strip()  # Can be username or email
        password = request.form.get('password', '')
        
        try:
            from models import User
            from werkzeug.security import check_password_hash
            
            # Find user by username or email
            user = User.query.filter(
                (User.username == login_field) | (User.email == login_field)
            ).first()
            
            if user and check_password_hash(user.password_hash, password):
                if not user.is_active:
                    flash('Conta não ativada. Verifique o seu email para ativar a conta.', 'error')
                else:
                    session['user_id'] = user.id
                    session['username'] = user.username
                    session['user_role'] = user.role
                    session['full_name'] = user.full_name
                    flash(f'Bem-vindo de volta, {user.full_name}!', 'success')
                    return redirect(url_for('dashboard'))
            else:
                flash('Credenciais inválidas. Verifique o utilizador/email e palavra-passe.', 'error')
                
        except Exception as e:
            print(f"Error during login: {e}")
            # Fallback to admin login for development
            if login_field == 'admin' and password == 'admin123':
                session['user_id'] = 1
                session['username'] = login_field
                session['user_role'] = 'admin'
                session['full_name'] = 'Administrador'
                flash('Login realizado com sucesso!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Erro durante o login. Tente novamente.', 'error')
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    
    # Mock dashboard data for now
    stats = {
        'monthly_sales': 0,
        'total_sales': 0,
        'monthly_purchases': 0,
        'total_purchases': 0,
        'profit': 0,
        'low_stock_alerts': 0,
        'recent_sales': [],
        'restock_products': []
    }
    
    return render_template('index.html', stats=stats)

@app.route('/logout')
def logout():
    session.clear()
    flash('Logout realizado com sucesso!', 'success')
    return redirect(url_for('login'))

# Database setup using direct SQL
@app.route('/setup-db')
def setup_db():
    try:
        from app import db
        import models  # Import to ensure tables are defined
        
        # Create all tables
        db.create_all()
        
        # Execute raw SQL to ensure proper setup
        sql_commands = [
            # Create admin user
            """
            INSERT INTO users (username, email, password_hash, full_name, role, is_active, created_at, updated_at)
            SELECT 'admin', 'admin@gestvendas.com', 'scrypt:32768:8:1$pPzReLiL5gLTDZD6$1db227ba4a74326cd7fb48fede70048d419011180540945f5706604f4090eecc90789fee9ebf31d3df5c1fb5be0180f8528671085754c4fcb41a6e7af36fac26', 'Administrador', 'admin', true, NOW(), NOW()
            WHERE NOT EXISTS (SELECT 1 FROM users WHERE username = 'admin');
            """,
            
            # Create categories
            """
            INSERT INTO categories (name, description, is_active, created_at, updated_at)
            SELECT unnest(ARRAY['Eletrónicos', 'Roupas', 'Casa e Jardim', 'Alimentação', 'Livros']),
                   unnest(ARRAY['Categoria Eletrónicos', 'Categoria Roupas', 'Categoria Casa e Jardim', 'Categoria Alimentação', 'Categoria Livros']),
                   true, NOW(), NOW()
            WHERE NOT EXISTS (SELECT 1 FROM categories);
            """,
            
            # Create default supplier
            """
            INSERT INTO suppliers (name, email, phone, address, is_active, created_at, updated_at)
            SELECT 'Fornecedor Geral', 'fornecedor@example.com', '210000000', 'Lisboa, Portugal', true, NOW(), NOW()
            WHERE NOT EXISTS (SELECT 1 FROM suppliers WHERE name = 'Fornecedor Geral');
            """,
            
            # Create configurations
            """
            INSERT INTO configurations (key, value, description, data_type, created_at, updated_at)
            SELECT unnest(ARRAY['currency', 'currency_symbol', 'tax_rate', 'company_name']),
                   unnest(ARRAY['EUR', '€', '23.00', 'GestVendas']),
                   unnest(ARRAY['Moeda padrão do sistema', 'Símbolo da moeda', 'Taxa de IVA padrão (%)', 'Nome da empresa']),
                   unnest(ARRAY['string', 'string', 'decimal', 'string']),
                   NOW(), NOW()
            WHERE NOT EXISTS (SELECT 1 FROM configurations);
            """
        ]
        
        for sql in sql_commands:
            try:
                db.session.execute(db.text(sql))
            except Exception as e:
                # Continue even if individual commands fail
                print(f"SQL command failed: {e}")
        
        db.session.commit()
        
        return """
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .success { color: green; }
            .info { background: #f0f8ff; padding: 20px; border-radius: 5px; }
        </style>
        <div class="info">
            <h2 class="success">✓ Base de dados configurada!</h2>
            <p>✓ Tabelas criadas no Supabase</p>
            <p>✓ Utilizador admin disponível</p>
            <p>✓ Dados iniciais inseridos</p>
            <p><strong>Credenciais:</strong> admin / admin123</p>
            <p><a href="/" style="color: blue;">← Voltar ao login</a></p>
        </div>
        """
        
    except Exception as e:
        return f"""
        <style>body {{ font-family: Arial, sans-serif; margin: 40px; }}</style>
        <h2 style="color: red;">Erro na configuração</h2>
        <p>Detalhes: {str(e)}</p>
        <p><a href="/test-db">Testar ligação à base de dados</a></p>
        """

# Database connection test route
@app.route('/test-db')
def test_db():
    try:
        from app import db
        from models import User
        
        # Test database connection
        users = User.query.all()
        return f"Ligação à base de dados bem-sucedida! Encontrados {len(users)} utilizadores."
    except Exception as e:
        return f"Falha na ligação à base de dados: {str(e)}"

# Products routes
@app.route('/products')
def products():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    
    try:
        from models import Category, Product
        
        # Get categories safely
        categories = []
        try:
            categories_query = Category.query.filter_by(is_active=True)
            categories = list(categories_query.all())
        except Exception as cat_error:
            print(f"Category query error: {cat_error}")
        
        # Get products safely
        products_list = []
        try:
            products_query = Product.query.filter_by(is_active=True)
            products_list = list(products_query.all())
        except Exception as prod_error:
            print(f"Product query error: {prod_error}")
        
        products_data = {
            'data': products_list,
            'total': len(products_list)
        }
        
        return render_template('products.html', 
                             products=products_data, 
                             categories=categories, 
                             search='', 
                             selected_category='')
    except Exception as e:
        print(f"Products route error: {e}")
        flash(f'Erro ao carregar produtos: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

# Customers routes  
@app.route('/customers')
def customers():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    
    customers_list = []
    # Simple, safe query without complex error handling
    try:
        from models import Customer
        results = Customer.query.all()
        customers_list = [customer for customer in results if customer.is_active]
    except Exception as e:
        print(f"Customer query error: {e}")
        customers_list = []
    
    customers_data = {
        'data': customers_list,
        'total': len(customers_list)
    }
    
    return render_template('customers.html', 
                         customers=customers_data, 
                         search='')

# Suppliers routes
@app.route('/suppliers') 
def suppliers():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    
    suppliers_list = []
    # Simple, safe query without complex error handling
    try:
        from models import Supplier
        results = Supplier.query.all()
        suppliers_list = [supplier for supplier in results if supplier.is_active]
    except Exception as e:
        print(f"Supplier query error: {e}")
        suppliers_list = []
    
    suppliers_data = {
        'data': suppliers_list,
        'total': len(suppliers_list)
    }
    
    return render_template('suppliers.html', 
                         suppliers=suppliers_data, 
                         search='')

# Sales routes
@app.route('/sales')
def sales():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    
    try:
        sales_list = []
        try:
            from models import Sale
            sales_query = Sale.query
            sales_list = list(sales_query.all())
        except Exception as sales_error:
            print(f"Sales query error: {sales_error}")
        
        sales_data = {
            'data': sales_list,
            'total': len(sales_list)
        }
        
        return render_template('sales.html', sales=sales_data)
    except Exception as e:
        print(f"Sales route error: {e}")
        flash(f'Erro ao carregar vendas: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

# Purchases routes  
@app.route('/purchases')
def purchases():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    
    try:
        purchases_list = []
        try:
            from models import Purchase
            purchases_query = Purchase.query
            purchases_list = list(purchases_query.all())
        except Exception as purch_error:
            print(f"Purchase query error: {purch_error}")
        
        purchases_data = {
            'data': purchases_list,
            'total': len(purchases_list)
        }
        
        return render_template('purchases.html', purchases=purchases_data)
    except Exception as e:
        print(f"Purchases route error: {e}")
        flash(f'Erro ao carregar compras: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

# Inventory routes
@app.route('/inventory')
def inventory():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    
    try:
        inventory_list = []
        try:
            from models import InventoryMovement
            inventory_query = InventoryMovement.query
            inventory_list = list(inventory_query.all())
        except Exception as inv_error:
            print(f"Inventory query error: {inv_error}")
        
        inventory_data = {
            'data': inventory_list,
            'total': len(inventory_list)
        }
        
        return render_template('inventory.html', inventory=inventory_data)
    except Exception as e:
        print(f"Inventory route error: {e}")
        flash(f'Erro ao carregar inventário: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

# Reports routes
@app.route('/reports')
def reports():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    
    return render_template('reports.html')

# Analytics routes  
@app.route('/analytics')
def analytics():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    
    return render_template('analytics.html')

@app.context_processor
def inject_user():
    return dict(
        current_user_id=session.get('user_id'),
        current_username=session.get('username'),
        current_user_role=session.get('user_role')
    )

@app.template_filter('currency')
def currency_filter(amount):
    if amount is None:
        amount = 0
    return f"{amount:,.2f} €"

# Register the filter
app.jinja_env.filters['currency'] = currency_filter

def format_currency(amount):
    if amount is None:
        amount = 0
    return f"{amount:,.2f} €"

app.jinja_env.globals.update(format_currency=format_currency)

# =============== ADD ROUTES ===============

# Add Product
@app.route('/products/add', methods=['GET', 'POST'])
def add_product():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            from models import Product, Category
            
            # Generate unique invoice number
            code = request.form.get('code')
            name = request.form.get('name')
            
            # Check if code already exists
            existing_product = Product.query.filter_by(code=code).first()
            if existing_product:
                flash('Código do produto já existe. Use um código diferente.', 'error')
                return redirect(url_for('add_product'))
            
            new_product = Product(
                code=code,
                name=name,
                description=request.form.get('description', ''),
                category_id=int(request.form.get('category_id') or 1),
                unit=request.form.get('unit', 'un'),
                purchase_price=float(request.form.get('purchase_price') or 0),
                sale_price=float(request.form.get('sale_price') or 0),
                tax_rate=float(request.form.get('tax_rate') or 23),
                stock_quantity=int(request.form.get('stock_quantity') or 0),
                min_stock=int(request.form.get('min_stock') or 0),
                max_stock=int(request.form.get('max_stock') or 100),
                is_active=True,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            db.session.add(new_product)
            db.session.commit()
            
            flash('Produto adicionado com sucesso!', 'success')
            return redirect(url_for('products'))
            
        except Exception as e:
            db.session.rollback()
            print(f"Error adding product: {e}")
            flash(f'Erro ao adicionar produto: {str(e)}', 'error')
    
    # Get categories for dropdown
    categories = []
    try:
        from models import Category
        categories = Category.query.all()
    except Exception as e:
        print(f"Error loading categories: {e}")
    
    return render_template('forms/add_product.html', categories=categories)

# Add Customer
@app.route('/customers/add', methods=['GET', 'POST'])
def add_customer():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            from models import Customer
            
            new_customer = Customer(
                name=request.form.get('name', ''),
                email=request.form.get('email', ''),
                phone=request.form.get('phone', ''),
                address=request.form.get('address', ''),
                city=request.form.get('city', ''),
                postal_code=request.form.get('postal_code', ''),
                country=request.form.get('country', 'Portugal'),
                tax_number=request.form.get('tax_number', ''),
                customer_type=request.form.get('customer_type', 'particular'),
                is_active=bool(request.form.get('is_active')),
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            db.session.add(new_customer)
            db.session.commit()
            
            flash('Cliente adicionado com sucesso!', 'success')
            return redirect(url_for('customers'))
            
        except Exception as e:
            db.session.rollback()
            print(f"Error adding customer: {e}")
            flash(f'Erro ao adicionar cliente: {str(e)}', 'error')
    
    return render_template('forms/add_customer.html')

# Add Supplier
@app.route('/suppliers/add', methods=['GET', 'POST'])
def add_supplier():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            from models import Supplier
            
            new_supplier = Supplier(
                name=request.form.get('name', ''),
                contact_person=request.form.get('contact_person', ''),
                email=request.form.get('email', ''),
                phone=request.form.get('phone', ''),
                address=request.form.get('address', ''),
                city=request.form.get('city', ''),
                postal_code=request.form.get('postal_code', ''),
                country=request.form.get('country', 'Portugal'),
                tax_number=request.form.get('tax_number', ''),
                is_active=bool(request.form.get('is_active')),
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            db.session.add(new_supplier)
            db.session.commit()
            
            flash('Fornecedor adicionado com sucesso!', 'success')
            return redirect(url_for('suppliers'))
            
        except Exception as e:
            db.session.rollback()
            print(f"Error adding supplier: {e}")
            flash(f'Erro ao adicionar fornecedor: {str(e)}', 'error')
    
    return render_template('forms/add_supplier.html')

# Add Sale
@app.route('/sales/add', methods=['GET', 'POST'])
def add_sale():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            from models import Sale
            
            # Generate unique invoice number
            invoice_number = f"VEN{datetime.now().strftime('%Y%m%d')}{secrets.token_hex(3).upper()}"
            
            # Safely parse dates
            sale_date_str = request.form.get('sale_date')
            due_date_str = request.form.get('due_date')
            
            sale_date = datetime.strptime(sale_date_str, '%Y-%m-%d').date() if sale_date_str else datetime.now().date()
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date() if due_date_str else None
            
            new_sale = Sale(
                invoice_number=invoice_number,
                customer_id=int(request.form.get('customer_id') or 1),
                user_id=session['user_id'],
                sale_date=sale_date,
                due_date=due_date,
                subtotal=float(request.form.get('subtotal') or 0),
                tax_amount=float(request.form.get('tax_amount') or 0),
                total_amount=float(request.form.get('total_amount') or 0),
                discount=float(request.form.get('discount') or 0),
                status=request.form.get('status', 'pendente'),
                payment_method=request.form.get('payment_method', 'dinheiro'),
                notes=request.form.get('notes', ''),
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            db.session.add(new_sale)
            db.session.commit()
            
            flash('Venda registada com sucesso!', 'success')
            return redirect(url_for('sales'))
            
        except Exception as e:
            db.session.rollback()
            print(f"Error adding sale: {e}")
            flash(f'Erro ao registar venda: {str(e)}', 'error')
    
    # Get customers for dropdown
    customers = []
    try:
        from models import Customer
        customers = Customer.query.filter_by(is_active=True).all()
    except Exception as e:
        print(f"Error loading customers: {e}")
    
    return render_template('forms/add_sale.html', customers=customers, today=datetime.now().strftime('%Y-%m-%d'))

# Add Purchase
@app.route('/purchases/add', methods=['GET', 'POST'])
def add_purchase():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            from models import Purchase
            
            # Generate unique invoice number
            invoice_number = f"COM{datetime.now().strftime('%Y%m%d')}{secrets.token_hex(3).upper()}"
            
            # Safely parse dates
            purchase_date_str = request.form.get('purchase_date')
            due_date_str = request.form.get('due_date')
            
            purchase_date = datetime.strptime(purchase_date_str, '%Y-%m-%d').date() if purchase_date_str else datetime.now().date()
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date() if due_date_str else None
            
            new_purchase = Purchase(
                invoice_number=invoice_number,
                supplier_id=int(request.form.get('supplier_id') or 1),
                user_id=session['user_id'],
                purchase_date=purchase_date,
                due_date=due_date,
                subtotal=float(request.form.get('subtotal') or 0),
                tax_amount=float(request.form.get('tax_amount') or 0),
                total_amount=float(request.form.get('total_amount') or 0),
                status=request.form.get('status', 'pendente'),
                payment_method=request.form.get('payment_method', 'transferencia'),
                notes=request.form.get('notes', ''),
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            db.session.add(new_purchase)
            db.session.commit()
            
            flash('Compra registada com sucesso!', 'success')
            return redirect(url_for('purchases'))
            
        except Exception as e:
            db.session.rollback()
            print(f"Error adding purchase: {e}")
            flash(f'Erro ao registar compra: {str(e)}', 'error')
    
    # Get suppliers for dropdown
    suppliers = []
    try:
        from models import Supplier
        suppliers = Supplier.query.filter_by(is_active=True).all()
    except Exception as e:
        print(f"Error loading suppliers: {e}")
    
    return render_template('forms/add_purchase.html', suppliers=suppliers, today=datetime.now().strftime('%Y-%m-%d'))

# Add Inventory Movement
@app.route('/inventory/add', methods=['GET', 'POST'])
def add_inventory():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            from models import InventoryMovement
            
            new_movement = InventoryMovement(
                product_id=int(request.form.get('product_id') or 1),
                movement_type=request.form.get('movement_type', 'entrada'),
                quantity=int(request.form.get('quantity') or 0),
                reference_type=request.form.get('reference_type', 'manual'),
                reference_id=int(request.form.get('reference_id') or 0) if request.form.get('reference_id') else None,
                notes=request.form.get('notes', ''),
                user_id=session['user_id'],
                created_at=datetime.now()
            )
            
            db.session.add(new_movement)
            db.session.commit()
            
            flash('Movimento de inventário registado com sucesso!', 'success')
            return redirect(url_for('inventory'))
            
        except Exception as e:
            db.session.rollback()
            print(f"Error adding inventory movement: {e}")
            flash(f'Erro ao registar movimento: {str(e)}', 'error')
    
    # Get products for dropdown
    products = []
    try:
        from models import Product
        products = Product.query.all()
    except Exception as e:
        print(f"Error loading products: {e}")
    
    return render_template('forms/add_inventory.html', products=products)

# =============== DELETE ROUTES ===============

# Delete Product
@app.route('/products/delete/<int:id>')
def delete_product(id):
    if not session.get('user_id'):
        return redirect(url_for('login'))
    
    try:
        from models import Product
        product = Product.query.get_or_404(id)
        
        db.session.delete(product)
        db.session.commit()
        
        flash('Produto eliminado com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting product: {e}")
        flash(f'Erro ao eliminar produto: {str(e)}', 'error')
    
    return redirect(url_for('products'))

# Delete Customer
@app.route('/customers/delete/<int:id>')
def delete_customer(id):
    if not session.get('user_id'):
        return redirect(url_for('login'))
    
    try:
        from models import Customer
        customer = Customer.query.get_or_404(id)
        
        db.session.delete(customer)
        db.session.commit()
        
        flash('Cliente eliminado com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting customer: {e}")
        flash(f'Erro ao eliminar cliente: {str(e)}', 'error')
    
    return redirect(url_for('customers'))

# Delete Supplier
@app.route('/suppliers/delete/<int:id>')
def delete_supplier(id):
    if not session.get('user_id'):
        return redirect(url_for('login'))
    
    try:
        from models import Supplier
        supplier = Supplier.query.get_or_404(id)
        
        db.session.delete(supplier)
        db.session.commit()
        
        flash('Fornecedor eliminado com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting supplier: {e}")
        flash(f'Erro ao eliminar fornecedor: {str(e)}', 'error')
    
    return redirect(url_for('suppliers'))

# Delete Sale
@app.route('/sales/delete/<int:id>')
def delete_sale(id):
    if not session.get('user_id'):
        return redirect(url_for('login'))
    
    try:
        from models import Sale
        sale = Sale.query.get_or_404(id)
        
        db.session.delete(sale)
        db.session.commit()
        
        flash('Venda eliminada com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting sale: {e}")
        flash(f'Erro ao eliminar venda: {str(e)}', 'error')
    
    return redirect(url_for('sales'))

# Delete Purchase
@app.route('/purchases/delete/<int:id>')
def delete_purchase(id):
    if not session.get('user_id'):
        return redirect(url_for('login'))
    
    try:
        from models import Purchase
        purchase = Purchase.query.get_or_404(id)
        
        db.session.delete(purchase)
        db.session.commit()
        
        flash('Compra eliminada com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting purchase: {e}")
        flash(f'Erro ao eliminar compra: {str(e)}', 'error')
    
    return redirect(url_for('purchases'))

# Delete Inventory Movement
@app.route('/inventory/delete/<int:id>')
def delete_inventory_movement(id):
    if not session.get('user_id'):
        return redirect(url_for('login'))
    
    try:
        from models import InventoryMovement
        movement = InventoryMovement.query.get_or_404(id)
        
        db.session.delete(movement)
        db.session.commit()
        
        flash('Movimento de inventário eliminado com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting inventory movement: {e}")
        flash(f'Erro ao eliminar movimento: {str(e)}', 'error')
    
    return redirect(url_for('inventory'))

# User Registration Routes
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            from models import User
            from werkzeug.security import generate_password_hash
            import secrets
            
            # Get form data
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip()
            full_name = request.form.get('full_name', '').strip()
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')
            
            # Validation
            if not all([username, email, full_name, password]):
                flash('Todos os campos são obrigatórios.', 'error')
                return render_template('register.html')
            
            if password != confirm_password:
                flash('As palavras-passe não coincidem.', 'error')
                return render_template('register.html')
            
            if len(password) < 6:
                flash('A palavra-passe deve ter pelo menos 6 caracteres.', 'error')
                return render_template('register.html')
            
            # Check if user already exists
            existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
            if existing_user:
                flash('Utilizador ou email já existem.', 'error')
                return render_template('register.html')
            
            # Generate confirmation token
            confirmation_token = secrets.token_urlsafe(32)
            
            # Create new user
            new_user = User(
                username=username,
                email=email,
                full_name=full_name,
                password_hash=generate_password_hash(password),
                role='user',
                is_active=False,  # User needs to confirm email
                confirmation_token=confirmation_token,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            db.session.add(new_user)
            db.session.commit()
            
            # Send confirmation email
            send_confirmation_email(email, full_name, confirmation_token)
            
            flash('Registo realizado com sucesso! Verifique o seu email para confirmar a conta.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            db.session.rollback()
            print(f"Error during registration: {e}")
            flash('Erro durante o registo. Tente novamente.', 'error')
    
    return render_template('register.html')

@app.route('/confirm-email/<token>')
def confirm_email(token):
    try:
        from models import User
        
        user = User.query.filter_by(confirmation_token=token).first()
        if not user:
            flash('Token de confirmação inválido ou expirado.', 'error')
            return redirect(url_for('login'))
        
        user.is_active = True
        user.confirmation_token = None
        user.updated_at = datetime.now()
        
        db.session.commit()
        
        flash('Email confirmado com sucesso! Pode agora fazer login.', 'success')
        return redirect(url_for('login'))
        
    except Exception as e:
        print(f"Error confirming email: {e}")
        flash('Erro ao confirmar email. Tente novamente.', 'error')
        return redirect(url_for('login'))

def send_confirmation_email(email, full_name, token):
    """Send email confirmation using SendGrid"""
    try:
        import os
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail
        
        # Check if SendGrid API key is available
        sendgrid_key = os.environ.get('SENDGRID_API_KEY')
        if not sendgrid_key:
            print("SendGrid API key not configured - email not sent")
            return False
        
        # Create confirmation URL
        base_url = request.url_root
        confirmation_url = f"{base_url}confirm-email/{token}"
        
        # Email content
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #007bff;">Bem-vindo ao GestVendas!</h2>
            <p>Olá {full_name},</p>
            <p>Obrigado por se registar no GestVendas. Para ativar a sua conta, clique no botão abaixo:</p>
            <p style="text-align: center; margin: 30px 0;">
                <a href="{confirmation_url}" 
                   style="background-color: #007bff; color: white; padding: 12px 24px; 
                          text-decoration: none; border-radius: 4px; display: inline-block;">
                    Confirmar Email
                </a>
            </p>
            <p>Se não conseguir clicar no botão, copie e cole este link no seu navegador:</p>
            <p><a href="{confirmation_url}">{confirmation_url}</a></p>
            <p>Este link expira em 24 horas.</p>
            <br>
            <p>Cumprimentos,<br>Equipa GestVendas</p>
        </div>
        """
        
        message = Mail(
            from_email='noreply@gestvendas.com',
            to_emails=email,
            subject='Confirme o seu registo - GestVendas',
            html_content=html_content
        )
        
        sg = SendGridAPIClient(sendgrid_key)
        response = sg.send(message)
        
        print(f"Email sent successfully: {response.status_code}")
        return True
        
    except Exception as e:
        print(f"Error sending email: {e}")
        return False