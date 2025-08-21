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

# Database setup and initialization
@app.route('/setup-db')
def setup_db():
    try:
        from app import db, init_database
        from models import User, Category, Supplier, Configuration
        
        # Initialize database tables
        success = init_database()
        if not success:
            return "Failed to create database tables"
        
        # Create default admin user
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
        
        # Create default categories
        categories = ['Eletrónicos', 'Roupas', 'Casa e Jardim', 'Alimentação', 'Livros']
        for cat_name in categories:
            if not Category.query.filter_by(name=cat_name).first():
                category = Category(name=cat_name, description=f'Categoria {cat_name}')
                db.session.add(category)
        
        # Create default supplier
        if not Supplier.query.filter_by(name='Fornecedor Geral').first():
            supplier = Supplier(
                name='Fornecedor Geral',
                email='fornecedor@example.com',
                phone='210000000',
                address='Lisboa, Portugal'
            )
            db.session.add(supplier)
        
        # Create default configurations
        default_configs = [
            {'key': 'currency', 'value': 'EUR', 'description': 'Moeda padrão do sistema'},
            {'key': 'currency_symbol', 'value': '€', 'description': 'Símbolo da moeda'},
            {'key': 'tax_rate', 'value': '23.00', 'description': 'Taxa de IVA padrão (%)', 'data_type': 'decimal'},
            {'key': 'company_name', 'value': 'GestVendas', 'description': 'Nome da empresa'},
        ]
        
        for config_data in default_configs:
            if not Configuration.query.filter_by(key=config_data['key']).first():
                config = Configuration(**config_data)
                db.session.add(config)
        
        db.session.commit()
        
        return """
        <h2>Base de dados configurada com sucesso!</h2>
        <p>✓ Tabelas criadas</p>
        <p>✓ Utilizador admin criado (admin/admin123)</p>
        <p>✓ Categorias padrão adicionadas</p>
        <p>✓ Configurações iniciais definidas</p>
        <p><a href="/">Voltar ao login</a></p>
        """
        
    except Exception as e:
        return f"Erro na configuração da base de dados: {str(e)}"

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