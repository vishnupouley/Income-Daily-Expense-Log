# views.py
from django.shortcuts import render
from django.http import HttpResponse
from faker import Faker
import random

# This will hold our data between requests
# In a real application, you'd use Django's session for this
PEOPLE_DATA = []

def generate_fake_data(count=50):
    """Generate fake data using Faker"""
    global PEOPLE_DATA
    fake = Faker()
    
    # Only generate data if we don't already have it
    if not PEOPLE_DATA:
        for _ in range(count):
            PEOPLE_DATA.append({
                'id': _ + 1,  # Just for reference
                'name': fake.name(),
                'email': fake.email(),
                'age': random.randint(18, 90),
                'job': fake.job(),
                'city': fake.city()
            })
    
    return PEOPLE_DATA

def index(request):
    """Main view to display the table"""
    # Generate data if we don't have it yet
    people = generate_fake_data()
    
    # Default sort
    current_sort = "name"
    
    return render(request, 'table_view.html', {
        'people': people,
        'current_sort': current_sort,
        'columns': ['name', 'email', 'age', 'job', 'city'],
        'verbose_names': {'name': 'Name', 'email': 'Email', 'age': 'Age', 'job': 'Job', 'city': 'City'},
    })

def sort_table(request):
    """Handle the sorting request from HTMX"""
    global PEOPLE_DATA
    
    # Get the sort field and direction from request
    sort_by = request.GET.get('sort', 'name')
    
    # This is our new current sort that will be returned to the client
    current_sort = sort_by
    
    # Remove the - prefix for actual sorting
    reverse_sort = False
    sort_field = sort_by
    if sort_by.startswith('-'):
        reverse_sort = True
        sort_field = sort_by[1:]
    
    # Sort the data
    if sort_field == 'age':
        # Sort numerically for age
        sorted_people = sorted(PEOPLE_DATA, key=lambda x: x[sort_field], reverse=reverse_sort)
    else:
        # Sort alphabetically for other fields
        sorted_people = sorted(PEOPLE_DATA, key=lambda x: str(x[sort_field]).lower(), reverse=reverse_sort)
    
    # Add HTMX specific headers to indicate we want to trigger events
    response = render(request, 'table_body_partial.html', {
        'people': sorted_people,
        'current_sort': current_sort
    })
    response['HX-Trigger'] = f'{{"currentSortChanged": "{current_sort}"}}'
    return response