FROM python:3.10

# Set work directory
WORKDIR /code

# Install dependencies
COPY requirements.txt .

RUN pip install -r requirements.txt

# Copy project
COPY src/ .


# Run the Django development server
CMD ["python", "manage.py", "runserver"]
