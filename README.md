# NOSS

## Introduction
This project provides a structured platform for developers seeking efficient project management and seamless collaboration in document and content handling. The platform centralizes essential project documents like initiation documents and requirements, ensuring accessibility and adherence to professional standards. The project also integrates AI for code bug detection, optimizing software development processes.

## Table of Contents
1. [Features](#features)
2. [Requirements](#requirements)
3. [Installation](#installation)
4. [Usage](#usage)
5. [Running Tests](#running-tests)
6. [Deployment](#deployment)
7. [Contributing](#contributing)
8. [License](#license)

## Features
- User Management: Custom user model with different personas (Manager, Developer), email verification, and blocking features.
- Project Management: Managers can create and manage projects, assign team members, and set up directories and files.
- Directory and File Management: Ability to create directories, upload files, and manage permissions for viewing and editing files.
- Task Management: Assign tasks to team members and send notifications/emails upon task assignment or completion.
- Notifications: Real-time notifications for users about task assignments, file uploads, and other project-related events.
- AI Code Improvement: Integration with OpenAI for code improvement, optimization, and bug detection.
- GitHub Integration: Upload, update, and delete files from GitHub repositories.
- SendGrid Integration: Send email notifications to users about important events like task assignments or file deletions.

## Requirements
Django==5.0.7
pytz==2018.9
sqlparse==0.4.3
pytest==7.0.1
pytest-django
requests
django-allauth
pipdeptree
python-dotenv
selenium
openai
sendgrid

## Installation

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/BS-PMC-2024/BS-PMC-2024-Team30.git
   cd project-repo

## Create a Virtual Environment:

python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`

## Install Dependencies:

pip install -r requirements.txt

## Set Up Environment Variables:
Create a .env file in the root directory with the following environment variables:

GITHUB_SECRET=your_github_secret
GITHUB_TOKEN=your_github_token
GITHUB_REPO=your_github_repo_name
EMAIL_USER=your_sendgrid_email
SENDGRID_API_KEY=your_sendgrid_api_key
OPENAI_API_KEY=your_openai_api_key

## Apply Migrations:

python manage.py migrate

## Create a Superuser:

python manage.py createsuperuser

## Run the Development Server:

python manage.py runserver

## Usage 

Access the Admin Panel:
Visit http://127.0.0.1:8000/admin and log in with your superuser credentials to manage users and projects.

Create and Manage Projects:
Project Managers and Admins can create, edit, delete, and manage projects via the main dashboard.

Manage Permissions:
Assign and manage permissions for team members to ensure secure and appropriate access to project resources.

Use AI for Code Bug Detection:
Utilize the integrated AI tools to detect and resolve code bugs within the project tasks.

## Running Tests
Unit Tests:
Run the unit tests to ensure all functionality is working as expected:
python manage.py test

Selenium Integration Tests:
Ensure that Selenium is installed and configured properly. Then run the integration tests:
pytest test_selenium.py

## Deployment


Jenkins CI/CD Pipeline:
The project includes a Jenkinsfile to automate the deployment process. Configure your Jenkins instance and integrate with your GitHub repository.

Deploy to Heroku:
This project can be deployed to Heroku by connecting your GitHub repository and configuring environment variables on the Heroku dashboard

## Contributing

We welcome contributions! Please follow these steps to contribute:
Fork the repository.
Create a new branch (git checkout -b feature-branch).
Make your changes and commit them (git commit -m 'Add feature').
Push to the branch (git push origin feature-branch).
Create a Pull Request.

## License


### Notes:
- **Replace** the placeholder values like `yourusername`, `project-repo`, `your_secret_key`, and `your_sendgrid_api_key` with actual values.
- If your project uses a different database (other than SQLite), update the `DATABASE_URL` accordingly.
- Ensure the requirements file (`requirements.txt`) is up to date with all necessary dependencies.
