from datetime import datetime
import secrets
import string

def format_currency(amount, currency_symbol='€'):
    """Format amount as currency with Euro symbol"""
    if amount is None:
        amount = 0
    return f"{amount:,.2f} {currency_symbol}".replace(',', ' ').replace('.', ',').replace(' ', '.')

def generate_invoice_number(prefix='V'):
    """Generate unique invoice number with prefix"""
    year = datetime.now().year
    timestamp = datetime.now().strftime('%m%d%H%M%S')
    random_part = ''.join(secrets.choice(string.digits) for _ in range(3))
    return f"{prefix}{year}{timestamp}{random_part}"

def calculate_totals(items):
    """Calculate subtotal, tax and total for a list of items"""
    subtotal = 0
    tax_total = 0
    
    for item in items:
        item_total = item['quantity'] * item['unit_price']
        item_tax = item_total * (item.get('tax_rate', 23) / 100)
        
        subtotal += item_total
        tax_total += item_tax
    
    return {
        'subtotal': subtotal,
        'tax_total': tax_total,
        'total': subtotal + tax_total
    }

def get_stock_status_class(stock_quantity, min_stock, max_stock):
    """Get CSS class for stock status"""
    if stock_quantity <= min_stock:
        return 'status-badge-danger'
    elif stock_quantity >= max_stock:
        return 'status-badge-warning'
    return 'status-badge-success'

def get_stock_status_text(stock_quantity, min_stock, max_stock):
    """Get text for stock status"""
    if stock_quantity <= min_stock:
        return 'Stock Baixo'
    elif stock_quantity >= max_stock:
        return 'Stock Alto'
    return 'Stock Normal'

def validate_tax_number(tax_number, country='PT'):
    """Basic validation for Portuguese tax numbers (NIF)"""
    if not tax_number:
        return True  # Optional field
    
    if country == 'PT':
        # Remove spaces and non-digits
        clean_number = ''.join(filter(str.isdigit, tax_number))
        
        # Portuguese NIF should have 9 digits
        if len(clean_number) != 9:
            return False
            
        # Basic check digit validation for Portuguese NIF
        digits = [int(d) for d in clean_number]
        check_sum = sum(digit * (9 - i) for i, digit in enumerate(digits[:-1]))
        check_digit = 11 - (check_sum % 11)
        
        if check_digit >= 10:
            check_digit = 0
            
        return check_digit == digits[-1]
    
    return True  # For other countries, accept any format

def format_date(date_obj, format_str='%d/%m/%Y'):
    """Format date object to Portuguese format"""
    if date_obj:
        return date_obj.strftime(format_str)
    return ''

def format_datetime(datetime_obj, format_str='%d/%m/%Y %H:%M'):
    """Format datetime object to Portuguese format"""
    if datetime_obj:
        return datetime_obj.strftime(format_str)
    return ''

def pagination_info(pagination):
    """Generate pagination information text"""
    if pagination.total == 0:
        return "Nenhum registo encontrado"
    
    start = (pagination.page - 1) * pagination.per_page + 1
    end = min(pagination.page * pagination.per_page, pagination.total)
    
    return f"Mostrando {start} a {end} de {pagination.total} registos"

def safe_float(value, default=0.0):
    """Safely convert value to float"""
    try:
        return float(value) if value else default
    except (ValueError, TypeError):
        return default

def safe_int(value, default=0):
    """Safely convert value to integer"""
    try:
        return int(value) if value else default
    except (ValueError, TypeError):
        return default
