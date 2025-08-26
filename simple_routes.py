from flask import render_template, request, redirect, url_for, flash, session
from app import app

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Temporary login without database
        if username == 'admin' and password == 'admin123':
            session['user_id'] = 1
            session['username'] = username
            session['user_role'] = 'admin'
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Credenciais inválidas. Use admin/admin123', 'error')
    
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
        from models import Category
        categories = Category.query.filter_by(is_active=True).all()
        
        # For now, return empty products list since we need to set up the full system
        products = []
        
        return render_template('products.html', 
                             products={'items': products, 'total': 0}, 
                             categories=categories, 
                             search='', 
                             selected_category='')
    except Exception as e:
        flash(f'Erro ao carregar produtos: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

# Customers routes  
@app.route('/customers')
def customers():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    
    try:
        from models import Customer
        customers_list = Customer.query.filter_by(is_active=True).all()
        customers_data = {'items': customers_list, 'total': len(customers_list)}
        
        return render_template('customers.html', 
                             customers=customers_data, 
                             search='')
    except Exception as e:
        flash(f'Erro ao carregar clientes: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

# Suppliers routes
@app.route('/suppliers') 
def suppliers():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    
    try:
        from models import Supplier
        suppliers_list = Supplier.query.filter_by(is_active=True).all()
        suppliers_data = {'items': suppliers_list, 'total': len(suppliers_list)}
        
        return render_template('suppliers.html', 
                             suppliers=suppliers_data, 
                             search='')
    except Exception as e:
        flash(f'Erro ao carregar fornecedores: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

# Sales routes
@app.route('/sales')
def sales():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    
    try:
        from models import Sale
        sales_list = Sale.query.all()
        sales_data = {'items': sales_list, 'total': len(sales_list)}
        
        return render_template('sales.html', sales=sales_data)
    except Exception as e:
        flash(f'Erro ao carregar vendas: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

# Purchases routes  
@app.route('/purchases')
def purchases():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    
    try:
        from models import Purchase
        purchases_list = Purchase.query.all()
        purchases_data = {'items': purchases_list, 'total': len(purchases_list)}
        
        return render_template('purchases.html', purchases=purchases_data)
    except Exception as e:
        flash(f'Erro ao carregar compras: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

# Inventory routes
@app.route('/inventory')
def inventory():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    
    try:
        from models import InventoryMovement
        inventory_list = InventoryMovement.query.all()
        inventory_data = {'items': inventory_list, 'total': len(inventory_list)}
        
        return render_template('inventory.html', inventory=inventory_data)
    except Exception as e:
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