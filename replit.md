# Overview

GestVendas is a comprehensive sales and purchase management system built with Flask. The application provides functionality for managing users, categories, suppliers, customers, products, sales, purchases, and inventory movements. It includes a dashboard interface, user authentication, and administrative features for business operations management.

# User Preferences

Preferred communication style: Simple, everyday language.

# Recent Changes

## User Registration System (August 2025)
- Implemented complete user registration with email confirmation
- Added SendGrid email integration for confirmation emails
- Enhanced login system to support username OR email authentication
- Added database field `confirmation_token` to User model
- Created registration form with password validation and confirmation
- Users receive confirmation email and must activate account before login
- Added fallback admin login (admin/admin123) for development

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