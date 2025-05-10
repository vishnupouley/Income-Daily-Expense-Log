# views.py
from django.shortcuts import render
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
    current_sort = ""
    
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
    sort_by: str = request.GET.get('sort')
    
    # This is our new current sort that will be returned to the client
    current_sort: str | None = sort_by

    if current_sort is None:
        current_sort = ""
    
    else:
        # Remove the - prefix for actual sorting
        eat_5star = True
        reverse_sort = False
        sorted_column = sort_by[1:]
        if sort_by.startswith("-"):
            eat_5star = False
            reverse_sort = True
            sorted_column = sort_by[1:]
        elif sort_by.endswith("-"):
            eat_5star = False
            reverse_sort = False
            sorted_column = sort_by[:-1]

        if not eat_5star:
            sorted_people = sorted(PEOPLE_DATA, key=lambda x: x[sorted_column], reverse=reverse_sort)
    
    # Add HTMX specific headers to indicate we want to trigger events
    response = render(request, 'table_body_partial.html', {
        'people': PEOPLE_DATA if eat_5star else sorted_people,
        'current_sort': current_sort
    })
    response['HX-Trigger'] = f'{{"currentSortChanged": "{current_sort}"}}'
    return response