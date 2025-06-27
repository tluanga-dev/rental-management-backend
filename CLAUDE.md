# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Development Server
```bash
cd src
PYTHONPATH=. python manage.py runserver
```

### Docker Development Environment
```bash
# Start all services (Django, PostgreSQL, Redis, Celery)
docker-compose up -d

# View logs
docker-compose logs -f web

# Run Django management commands
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser

# Restart services
docker-compose restart web

# Stop all services
docker-compose down
```

### Database Operations
```bash
cd src
PYTHONPATH=. python manage.py makemigrations  # Create new migrations
PYTHONPATH=. python manage.py migrate         # Apply migrations
```

### Testing
```bash
cd src
PYTHONPATH=. python manage.py test                    # Run all tests
PYTHONPATH=. python manage.py test apps.customer       # Run tests for specific app
PYTHONPATH=. python manage.py test apps.customer.tests.test_models  # Run specific test module

# Docker testing
docker-compose exec web python manage.py test
```

### Linting and Type Checking
```bash
# Run linting
cd src
ruff check .
ruff format .

# Run type checking
mypy .
```

### Custom Management Commands
```bash
cd src
PYTHONPATH=. python manage.py create_admin_accounts   # Create default admin accounts
PYTHONPATH=. python manage.py setup_periodic_tasks     # Setup Celery periodic tasks
PYTHONPATH=. python manage.py test_celery             # Test Celery configuration
PYTHONPATH=. python manage.py toggle_auth             # Toggle authentication (dev utility)
PYTHONPATH=. python manage.py load_units              # Load units of measurement
```

### Static Files (for production)
```bash
cd src
PYTHONPATH=. python manage.py collectstatic --noinput
```

## Architecture Overview

This is a Django REST Framework backend for a rental management system. The architecture follows Django's app-based structure with clear separation of concerns.

### Core Components

1. **Authentication System**: JWT-based authentication using djangorestframework-simplejwt. Custom authentication viewset in `apps/core/views/auth.py` handles login, token refresh, and logout with blacklisting.

2. **Base Classes**: Located in `apps/base/`, providing:
   - `BaseViewSet`: Standard viewset with pagination and permissions
   - `TimeStampedModel`: Abstract model with created_at/updated_at fields
   - `CustomPagination`: Consistent pagination across all endpoints

3. **Permission System**: Custom permission classes in `apps/core/permissions.py` implementing role-based access control.

4. **ID Generation**: Centralized ID generation system in `apps/id_manager/` using prefixes and counters for different entity types.

### Business Domain Apps

Each app follows a consistent structure with models, serializers, views, admin, and tests:
- **customer**: Customer management with soft delete capability
- **vendor**: Vendor management 
- **warehouse**: Warehouse/location management
- **item_category**: Hierarchical item categorization
- **item_packaging**: Item packaging definitions
- **unit_of_measurement**: Units management with custom fixtures
- **inventory_item**: Inventory management with master items, instances, and stock movements
- **purchases**: Purchase transaction management with line items and warranty tracking

### Background Processing

Celery is configured for async task processing with Redis as the message broker. Tasks are defined in `apps/core/tasks.py` and periodic tasks are managed via Django admin.

### API Structure

All API endpoints follow RESTful conventions with:
- JWT authentication required (except for auth endpoints)
- Consistent error responses
- Pagination on list endpoints
- API documentation available via drf-spectacular

### Database

- Development: SQLite (default)
- Production: PostgreSQL support configured
- Migrations tracked in each app's migrations/ directory
- Docker: PostgreSQL as primary database with Redis for caching/Celery

## API Endpoints

### Core Endpoints
- `GET /` - Health check
- `GET /api/` - API information
- `GET /api/docs/` - Swagger UI documentation
- `GET /api/redoc/` - ReDoc documentation
- `GET /api/schema/` - OpenAPI schema

### Authentication (JWT-based)
- `POST /api/auth/login/` - User login (returns access & refresh tokens)
- `POST /api/auth/register/` - User registration
- `POST /api/auth/refresh/` - Refresh access token
- `POST /api/auth/verify/` - Verify token validity
- `POST /api/auth/logout/` - Logout and blacklist refresh token

### Business Domain Endpoints

#### Customer Management
- `GET /api/customers/` - List all customers
- `POST /api/customers/` - Create new customer
- `GET /api/customers/{id}/` - Get customer details
- `PUT /api/customers/{id}/` - Update customer
- `DELETE /api/customers/{id}/` - Soft delete customer

#### Vendor Management
- `GET /api/vendors/` - List all vendors
- `POST /api/vendors/` - Create new vendor
- `GET /api/vendors/{id}/` - Get vendor details
- `PUT /api/vendors/{id}/` - Update vendor
- `DELETE /api/vendors/{id}/` - Delete vendor

#### Warehouse Management
- `GET /api/warehouses/` - List all warehouses
- `POST /api/warehouses/` - Create new warehouse
- `GET /api/warehouses/{id}/` - Get warehouse details
- `PUT /api/warehouses/{id}/` - Update warehouse
- `DELETE /api/warehouses/{id}/` - Delete warehouse

#### Item Categories
- `GET /api/items/categories/` - List all categories
- `POST /api/items/categories/` - Create new category
- `GET /api/items/subcategories/` - List all subcategories
- `POST /api/items/subcategories/` - Create new subcategory

#### Inventory Management
- `GET /api/inventory/inventory-masters/` - List inventory master items
- `POST /api/inventory/inventory-masters/` - Create inventory master
- `GET /api/inventory/inventory-items/` - List inventory instances
- `POST /api/inventory/inventory-items/` - Create inventory instance
- `GET /api/inventory/inventory-movements/` - List stock movements
- `POST /api/inventory/inventory-movements/` - Record stock movement

#### Purchase Management
- `GET /api/purchases/transactions/` - List purchase transactions
- `POST /api/purchases/transactions/` - Create purchase transaction
- `GET /api/purchases/transaction-items/` - List transaction line items
- `POST /api/purchases/transaction-items/` - Add transaction line item

#### Supporting Endpoints
- `GET /api/unit-of-measurement/` - List units of measurement
- `GET /api/packaging/` - List packaging types

## Testing Guidelines

### Running Tests

#### Unit Tests
```bash
# Test individual apps
docker-compose exec web python manage.py test apps.inventory_item
docker-compose exec web python manage.py test apps.purchases

# Test specific test classes
docker-compose exec web python manage.py test apps.inventory_item.tests.test_models
docker-compose exec web python manage.py test apps.purchases.tests.test_views
```

#### Integration Tests
```bash
# Test API endpoints
docker-compose exec web python manage.py test apps.inventory_item.tests.test_api
docker-compose exec web python manage.py test apps.purchases.tests.test_api
```

### Test Coverage
```bash
# Generate coverage report
docker-compose exec web coverage run --source='.' manage.py test
docker-compose exec web coverage report
docker-compose exec web coverage html
```

### Testing New Features

When adding new features, ensure comprehensive testing:

1. **Model Tests** (`test_models.py`):
   - Test model creation and field validation
   - Test model methods and properties
   - Test model constraints and indexes
   - Test signal handlers if any

2. **Serializer Tests** (`test_serializers.py`):
   - Test serialization of model instances
   - Test deserialization and validation
   - Test nested serializers
   - Test custom field methods

3. **View/API Tests** (`test_views.py` or `test_api.py`):
   - Test CRUD operations
   - Test authentication and permissions
   - Test filtering, searching, and ordering
   - Test pagination
   - Test error handling
   - Test edge cases

4. **Integration Tests**:
   - Test complete workflows
   - Test transactions and data consistency
   - Test background task execution

### Example Test Structure
```python
from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status

class InventoryItemModelTest(TestCase):
    def setUp(self):
        # Setup test data
        pass
    
    def test_create_inventory_item(self):
        # Test model creation
        pass
    
    def test_model_constraints(self):
        # Test business logic constraints
        pass

class InventoryItemAPITest(APITestCase):
    def setUp(self):
        # Setup test client and data
        pass
    
    def test_list_inventory_items(self):
        # Test GET request
        pass
    
    def test_create_inventory_item(self):
        # Test POST request
        pass
```

## Development Workflow

### Adding New Apps
1. Create app in `apps/` directory: `django-admin startapp <app_name>`
2. Update `apps.py` to use `apps.<app_name>` namespace
3. Add to `INSTALLED_APPS` in both `settings.py` and `settings_docker.py`
4. Create models following the established patterns
5. Create serializers, views, and URLs
6. Register models in admin.py
7. Create and run migrations
8. Write comprehensive tests
9. Update API documentation

### Code Quality Checks
Before committing:
1. Run linting: `ruff check .`
2. Run formatting: `ruff format .`
3. Run tests: `python manage.py test`
4. Check migrations: `python manage.py makemigrations --check`

### Environment Variables
Key environment variables for Docker:
- `DJANGO_SETTINGS_MODULE=config.settings_docker`
- `DEBUG=True/False`
- `ENABLE_AUTHENTICATION=True/False`
- `DB_NAME`, `DB_USER`, `DB_PASSWORD`
- `CELERY_BROKER_URL`
- `SECRET_KEY`

### Common Issues and Solutions

1. **Import Errors**: Ensure all imports use `apps.` prefix
2. **Migration Conflicts**: Always pull latest changes before creating new migrations
3. **Docker Port Conflicts**: Backend runs on port 9000 by default
4. **Authentication Issues**: Check `ENABLE_AUTHENTICATION` environment variable
5. **Celery Task Failures**: Verify Redis is running and CELERY_BROKER_URL is correct