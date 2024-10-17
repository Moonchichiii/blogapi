# 🚀 BlogClient Backend: Powering the Social Blogging Platform

## 🌟 Quick Links
- [Live Project]() (Coming Soon!)
- [Project Board](https://github.com/users/Moonchichiii/projects/39)
- [API Documentation](docs/api_readme.md)
- [Deployment Guide](docs/deployment_guide.md)

## 🎯 Project Overview
BlogClient Backend is the powerhouse behind a dynamic social media blogging platform. Built with Django and DRF, it offers robust features for a seamless blogging experience.

### 🔑 Key Features
- Secure JWT-based authentication with email verification & 2FA authentication.
- Post creation, commenting, and user tagging
- Rating system for posts
- Follow system and content discovery
- High-level security measures
- Efficient caching strategies
- Admin tools for content moderation
- Popularity metrics for users and posts
- Notification system

## 🏗️ Application Structure

```
blogclient_backend/
│
├── accounts/
├── profiles/
├── posts/
├── comments/
├── ratings/
├── tags/
├── followers/
├── notifications/
├── popularity/
│
├── backend/
│   ├── settings.py
│   ├── urls.py
│   └── celery.py
│
├── static/
├── media/
│
├── manage.py
├── requirements.txt
└── README.md
```

## 🛠️ Tech Stack
- Django & Django REST Framework
- SQLite (for development, can be easily switched to PostgreSQL for production)
- JWT Authentication
- Redis for caching and Celery tasks
- Cloudinary for media storage
- Celery for asynchronous tasks

## 📦 Key Dependencies
- Django
- Django REST Framework
- Django REST Framework SimpleJWT
- Cloudinary
- Celery
- Redis
- Pillow

## 🚀 Quick Start
1. Clone: `git clone https://github.com/yourusername/blogclient-backend.git`
2. Install: `pip install -r requirements.txt`
3. Migrate: `python manage.py migrate`
4. Run: `python manage.py runserver`

## 🧪 Testing
Project has an extensive test suite with 96% coverage. Key testing features include:

- Comprehensive unit tests for all applications
- Integration tests for API endpoints
- Mocking of external services and tasks
- Custom test cases for model methods and signals

To run the tests:
```
python manage.py test
```

For a coverage report:
```
coverage run --source='.' manage.py test
coverage report
```

## 🔒 Security Features
- Email verification for new accounts
- JWT with access and refresh tokens
- Password validation with custom requirements
- CORS configuration
- Cloudinary secure URLs for media

## 📦 Deployment
This project is designed to be deployed on a platform of your choice. Key considerations:

1. Update `ALLOWED_HOSTS` in `settings.py`
2. Configure environment variables
3. Set `DEBUG = False` for production
4. Set up a production-ready database (e.g., PostgreSQL)
5. Configure Celery and Redis for production

## 🔮 Future Enhancements
- Enhance the popularity algorithm
- Implement more advanced caching strategies


## 📜 License
This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.

---

Built with ❤️