# BlogClient Backend

## 👉 [Link to Live Project]()

## 👉 [Project Board link](https://github.com/users/Moonchichiii/projects/39)

## Table of Contents

1. [Project Overview](#project-overview)
 - [Objective](#objective)
 - [User Interaction](#user-interaction)
 - [Administrative Features](#administrative-features)
 - [Future Enhancements](#future-enhancements)
2. [Design & Planning](#design-and-planning)
 - [Kanban Board](#kanban-board)
 - [Data Models](#data-models)
 - [API Endpoints](#api-endpoints)
3. [Technologies](#technologies)
4. [Dependencies](#dependencies)
5. [Setup and Installation](#setup-and-installation)
 - [Clone the Repository](#clone-the-repository)
 - [Install Dependencies](#install-dependencies)
 - [Run Migrations](#run-migrations)
 - [Start the Development Server](#start-the-development-server)
6. [Testing](#testing)
 - [Django Testing](#django-testing)
7. [Deployment](#deployment)
 - [Heroku Deployment](#heroku-deployment)
 - [Create a Heroku App](#create-a-heroku-app)
 - [Add PostgreSQL Addon](#add-postgresql-addon)
 - [Build and Deploy](#build-and-deploy)
 - [Configure Environment Variables](#configure-environment-variables)
 - [Post-Deployment](#post-deployment)
8. [Credits](#credits)

## Project Overview

### Objective

The **BlogClient Backend** serves as the API and data management layer for the BlogClient platform. It handles user authentication, post creation, interactions, and content moderation.

#### User Interaction

- **User Registration and Authentication:**
 - JWT-based authentication for secure API access.
 - Profile management for updating user information.

- **Create Posts:**
 - API endpoints for creating, updating, and deleting posts.
 - Tagging system for mentioning users in posts.

- **Comments and Ratings:**
 - API endpoints for commenting on posts and rating content.

- **Follow Other Profiles:**
 - System for following/unfollowing users and retrieving follower lists.

- **Explore and Discover:**
 - Search and filter functionality for discovering content.

### Administrative Features

- **User Management:**
 - Django Admin interface for managing users and content.
 - Content moderation tools for approving/rejecting posts.

- **Analytics Insights:**
 - Tracking user activity, post interactions, and other metrics.

### Future Enhancements

- **Advanced Analytics:** Provide detailed analytics for users and admins.
- **Notification System:** Implement notifications for user interactions and content updates.

[Back to top](#table-of-contents)

## Design and Planning

### Kanban Board

- **Development Process:** The project follows an agile approach, with tasks managed on a Kanban board.
- **Development Preparation:** Initial steps included planning data models and API architecture.
- **Feature Tracking & Task Management:** Tasks are categorized and moved through stages (Todo, In Progress, Done).

👉 [Project Board link](https://github.com/users/Moonchichiii/projects/39)

### Data Models

- **User Model:** Handles user data and authentication.
- **Profile Model:** Stores additional user information like bio and profile picture.
- **Post Model:** Manages the creation, updating, and deletion of blog posts.
- **Comment Model:** Handles comments on posts.
- **Tag Model:** Enables tagging users in posts.

### API Endpoints

- **User Endpoints:**
 - `/api/register/` - Register a new user.
 - `/api/login/` - Authenticate a user and return a JWT token.
 - `/api/profile/` - Retrieve and update user profiles.

- **Post Endpoints:**
 - `/api/posts/` - Create, update, delete, and retrieve posts.
 - `/api/posts/<id>/comments/` - Add comments to a post.

- **Follow Endpoints:**
 - `/api/follow/` - Follow or unfollow a user.
 - `/api/followers/` - Retrieve a list of followers.

[Back to top](#table-of-contents)

## Technologies

- **Django:** Python web framework used for building the backend.
- **Django REST Framework:** Toolkit for building Web APIs.
- **PostgreSQL:** Database system used in production.
- **JWT:** JSON Web Tokens for authentication.

## Dependencies

- **Django**: Main web framework for building the backend.
- **Django REST Framework**: Tools for building APIs.
- **djangorestframework-simplejwt**: JWT authentication for Django REST Framework.
- **PostgreSQL**: Relational database system for data storage.
- **django-cors-headers**: Handles Cross-Origin Resource Sharing (CORS).
- **django-environ**: Environment variables management.

[Back to top](#table-of-contents)

## Setup and Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/blogclient-backend.git`` 

2.  **Install Dependencies**
    
    bash
    
    Copy code
    
    `pip install -r requirements.txt` 
    
3.  **Run Migrations**
    
    bash
    
    Copy code
    
    `python manage.py migrate` 
    
4.  **Start the Development Server**
    
    bash
    
    Copy code
    
    `python manage.py runserver` 
    

[Back to top](#table-of-contents)

## Testing

### Django Testing

-   **Unit Tests:** Implement unit tests for models and views.
-   **Integration Tests:** Ensure that API endpoints function as expected.
-   **Run Tests:**
    
    bash
    
    Copy code
    
    `python manage.py test` 
    

[Back to top](#table-of-contents)

## Deployment

### Heroku Deployment

#### Create a Heroku App

-   **Login to Heroku** and create a new app.

#### Add PostgreSQL Addon

-   **Add the PostgreSQL addon** to your Heroku app for database management.

#### Build and Deploy

-   **Push your code** to Heroku and run migrations.
    
    bash
    
    Copy code
    
    `git push heroku main
    heroku run python manage.py migrate` 
    

#### Configure Environment Variables

-   **Set environment variables** like `DATABASE_URL`, `SECRET_KEY`, and others using the Heroku dashboard.

#### Post-Deployment

-   **Monitor the app** using Heroku’s dashboard and logs.

[Back to top](#table-of-contents)

## Credits

Special thanks to the Django and Django REST Framework communities for their extensive documentation and support.

[Back to top](#table-of-contents)
