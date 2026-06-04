
import os
import sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'civilproject.settings')
import django
django.setup()
print("Django setup successful!")

from django.urls import get_resolver
resolver = get_resolver()
print("URL resolver loaded successfully!")

print("Available URL patterns:")
for pattern in resolver.url_patterns:
    print(f"  - {pattern}")
