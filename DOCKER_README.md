# Docker Setup for Rental Backend

This guide explains how to run the rental backend using Docker and Docker Compose.

## Prerequisites

- Docker installed on your system
- Docker Compose installed on your system

## Quick Start

1. **Clone the repository** (if you haven't already)

2. **Copy environment variables**:
   ```bash
   cp .env.example .env
   ```
   
3. **Edit the `.env` file** with your desired configuration (especially change the SECRET_KEY and passwords for production)

4. **Build and run the containers**:
   ```bash
   docker-compose up --build
   ```

   This will:
   - Build the Django application image
   - Start PostgreSQL database
   - Start Redis for caching and Celery
   - Run database migrations
   - Collect static files
   - Create a superuser (if it doesn't exist)
   - Start the Django development server
   - Start Celery worker and beat scheduler

5. **Access the application**:
   - Django application: http://localhost:8000
   - API documentation: http://localhost:8000/api/docs/
   - Admin interface: http://localhost:8000/admin/

## Common Commands

### Run in detached mode
```bash
docker-compose up -d
```

### View logs
```bash
docker-compose logs -f
```

### Stop containers
```bash
docker-compose down
```

### Stop and remove volumes
```bash
docker-compose down -v
```

### Run Django management commands
```bash
docker-compose exec web python manage.py <command>
```

### Create a new superuser
```bash
docker-compose exec web python manage.py createsuperuser
```

### Run tests
```bash
docker-compose exec web python manage.py test
```

### Access Django shell
```bash
docker-compose exec web python manage.py shell
```

### Access PostgreSQL
```bash
docker-compose exec db psql -U rental_user -d rental_db
```

### Rebuild a specific service
```bash
docker-compose build web
```

## Services

The Docker Compose setup includes the following services:

1. **db**: PostgreSQL 15 database
2. **redis**: Redis 7 for caching and Celery message broker
3. **web**: Django application server (Gunicorn)
4. **celery**: Celery worker for background tasks
5. **celery-beat**: Celery beat scheduler for periodic tasks

## Volumes

The setup uses named volumes for data persistence:

- `postgres_data`: PostgreSQL database files
- `static_volume`: Django static files
- `media_volume`: User uploaded media files

## Production Considerations

For production deployment:

1. Change `DEBUG=False` in `.env`
2. Use strong passwords and secret keys
3. Configure proper `ALLOWED_HOSTS`
4. Use a production-grade web server (nginx) in front of Gunicorn
5. Configure SSL/TLS certificates
6. Set up proper logging and monitoring
7. Configure backup strategies for the database
8. Consider using managed database services

## Troubleshooting

### Import errors
If you encounter import errors, ensure:
- All Django apps have the `apps.` prefix in INSTALLED_APPS
- URL includes use the correct app paths
- The Django settings module is correctly set

### Database connection errors
- Ensure the database service is healthy before the web service starts
- Check that environment variables are correctly set
- Verify PostgreSQL credentials match in `.env`

### Static files not loading
- Run `docker-compose exec web python manage.py collectstatic`
- Check that WhiteNoise middleware is properly configured

### Celery not processing tasks
- Check Redis connection
- Verify Celery is finding tasks correctly
- Check logs: `docker-compose logs celery`