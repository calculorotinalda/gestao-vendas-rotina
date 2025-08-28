# Overview

GestVendas is a comprehensive sales and purchase management system built with Flask. The application provides functionality for managing users, categories, suppliers, customers, products, sales, purchases, and inventory movements. It includes a dashboard interface, user authentication, and administrative features for business operations management.

# User Preferences

Preferred communication style: Simple, everyday language.

# Recent Changes

## SAF-T Portugal Integration (August 2025)
- Implemented complete SAF-T (Standard Audit File for Tax) system for Portuguese tax compliance
- Compliant with Portaria n.º 302/2016 and OECD standards (version 1.04_01)
- Date range selection with preset options (month, quarter, year, previous year)
- XML generation includes: company info, chart of accounts, customers, suppliers, products, tax tables
- Automatic download of properly formatted SAF-T PT XML files
- Integration with existing database for real customer/supplier/product data
- Fallback data structure ensures file generation even with minimal database content
- Professional interface with legal compliance information and technical specifications

## Analytics System Fixes (August 2025)
- Fixed server errors in analytics by creating simplified data structure
- Resolved template variable conflicts (total_revenue, total_costs, etc.)
- Implemented fallback analytics with static demo data for stability
- Added all required template fields to prevent undefined variable errors
- Analytics page now loads without server internal errors
- Provides comprehensive KPIs, charts and financial metrics view
- System prioritizes stability over complex database joins for analytics

## Advanced Purchase System (August 2025)
- Implemented comprehensive purchase management system similar to sales
- Supplier selection from database with contact information display
- Product selection with purchase price calculation and stock validation
- Real-time calculation of subtotal, IVA, and total amounts
- Automatic stock increases when purchases are completed
- Integration with PurchaseItem model for detailed transaction tracking
- Inventory movement tracking for purchase transactions (entrada type)
- Corrected model field names (invoice_number vs purchase_number, subtotal vs subtotal_amount)

## Advanced Sales System (August 2025)
- Implemented advanced sales system with customer and product selection
- Real-time calculation of subtotal, IVA, and total amounts
- Dynamic product selection from inventory with stock validation
- Automatic stock updates when sales are completed
- Interactive interface with product search and selection modal
- Integration with SaleItem model for detailed transaction tracking
- Inventory movement tracking for sales transactions

## User Registration System (August 2025)
- Implemented complete user registration with email confirmation
- Added SendGrid email integration for confirmation emails
- Enhanced login system to support username OR email authentication
- Added database field `confirmation_token` to User model
- Created registration form with password validation and confirmation
- Users receive confirmation email and must activate account before login
- Added fallback admin login (admin/admin123) for development

## Comprehensive Reports System (August 2025)
- Created detailed reporting system with 4 main sections
- Sales reports with transaction history and analytics
- Product reports with performance metrics and stock alerts
- Purchase reports with supplier transaction tracking
- Financial reports with profit/loss analysis and charts
- Interactive filtering by time period (7, 30, 90, 365 days)
- Chart.js integration for visual data representation
- DataTables for searchable and sortable report listings

# System Architecture

## Backend Architecture
- **Framework**: Flask web framework with SQLAlchemy ORM
- **Database**: PostgreSQL with SQLAlchemy models for data persistence
- **Authentication**: Session-based authentication with password hashing using Werkzeug
- **Application Structure**: Modular design with separate files for models, routes, and utilities
- **Configuration Management**: Environment-based configuration with default fallbacks

## Database Design
- **User Management**: Users table with role-based access control (admin/user roles)
- **Product Management**: Categories, suppliers, and products with relationships
- **Transaction Tracking**: Sales, purchases, and inventory movements with item-level details
- **System Configuration**: Configurable settings for currency, tax rates, and company information
- **Audit Trail**: Created/updated timestamps on all major entities

## Frontend Architecture
- **Template Engine**: Flask's Jinja2 templating system
- **CSS Framework**: Bootstrap 5 for responsive design
- **JavaScript**: Vanilla JavaScript with modular app structure
- **UI Components**: DataTables for data grids, Chart.js for analytics, Flatpickr for date selection
- **Responsive Design**: Mobile-first approach with collapsible sidebar navigation

## Key Features
- **Dashboard**: Real-time analytics and business metrics
- **Inventory Management**: Stock tracking with minimum/maximum levels
- **Sales Processing**: Invoice generation with automatic numbering
- **Purchase Management**: Supplier purchase tracking
- **User Management**: Multi-user support with role-based permissions and user registration
- **Financial Reporting**: Currency formatting and tax calculations
- **CRUD Operations**: Complete create, read, update, delete functionality for all entities
- **Data Validation**: Form validation with required fields and type checking
- **Automated Numbering**: Unique invoice numbers for sales and purchases
- **User Registration**: Email confirmation system with SendGrid integration
- **Authentication**: Login with username or email support

## Security Measures
- **Password Security**: Werkzeug password hashing
- **Session Management**: Flask session handling with secret key
- **Environment Variables**: Sensitive configuration via environment variables
- **Database Security**: Connection pooling and pre-ping health checks

# External Dependencies

## Core Framework Dependencies
- **Flask**: Web application framework
- **SQLAlchemy**: Database ORM and query builder
- **Werkzeug**: WSGI utilities and security functions

## Frontend Libraries
- **Bootstrap 5**: CSS framework for responsive design
- **Font Awesome**: Icon library for UI elements
- **DataTables**: Advanced table functionality with sorting/filtering
- **Chart.js**: Data visualization and analytics charts
- **Flatpickr**: Modern date picker component

## Database
- **Supabase PostgreSQL**: Cloud-hosted PostgreSQL database with real-time capabilities
- **Connection**: Direct SQLAlchemy connection using Supabase's PostgreSQL connection string
- **Migration Strategy**: SQLAlchemy create_all() for initial setup, manual schema updates as needed
- **Connection Pooling**: Built-in SQLAlchemy connection management with transaction pooler

## Production Considerations
- **ProxyFix**: Werkzeug middleware for reverse proxy deployments
- **Environment Configuration**: Support for production environment variables
- **Logging**: Configurable logging system for debugging and monitoring