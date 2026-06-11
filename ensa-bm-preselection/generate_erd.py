import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.apps import apps
from django.db.models.fields.related import ForeignKey, OneToOneField, ManyToManyField

print("```mermaid")
print("erDiagram")

app_labels = ['users', 'candidatures', 'administration', 'scoring', 'notifications']
models = apps.get_models()

for model in models:
    if model._meta.app_label not in app_labels:
        continue
    
    model_name = model.__name__
    print(f"    {model_name} {{")
    for field in model._meta.fields:
        field_type = field.get_internal_type()
        print(f"        {field_type} {field.name}")
    print("    }")

    for field in model._meta.get_fields():
        if field.is_relation and (isinstance(field, ForeignKey) or isinstance(field, OneToOneField) or isinstance(field, ManyToManyField)):
            if field.related_model and field.related_model._meta.app_label in app_labels:
                related_name = field.related_model.__name__
                if isinstance(field, ForeignKey):
                    print(f"    {related_name} ||--o{{ {model_name} : \"{field.name}\"")
                elif isinstance(field, OneToOneField):
                    print(f"    {related_name} ||--|| {model_name} : \"{field.name}\"")
                elif isinstance(field, ManyToManyField):
                    print(f"    {related_name} }}o--o{{ {model_name} : \"{field.name}\"")

print("```")
