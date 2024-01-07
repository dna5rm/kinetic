# Setup Environment
Create new project: django-admin startproject mysite
To start: manage.py runserver

# Setup App under environment
manage.py startapp main

main > views.py > +def index(response): > return HttpResponse("<h1>hello world</h1>")
main > urls.py > +from . import views
main > urls.py > urlpatterns > +path("", views.index, name="index"),

mysite > urls.py > +from django.urls import path, include
mysite > urls.py > urlpatterns > +path('', include("main.urls")),

# SQLite Database
Edit: setting.py > INSTALLED_APPS > add <app>.apps.MainConfig
./manage.py migrate
Operations to perform:
  Apply all migrations: admin, auth, contenttypes, sessions
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying auth.0001_initial... OK
  Applying admin.0001_initial... OK
  Applying admin.0002_logentry_remove_auto_add... OK
  Applying admin.0003_logentry_add_action_flag_choices... OK
  Applying contenttypes.0002_remove_content_type_name... OK
  Applying auth.0002_alter_permission_name_max_length... OK
  Applying auth.0003_alter_user_email_max_length... OK
  Applying auth.0004_alter_user_username_opts... OK
  Applying auth.0005_alter_user_last_login_null... OK
  Applying auth.0006_require_contenttypes_0002... OK
  Applying auth.0007_alter_validators_add_error_messages... OK
  Applying auth.0008_alter_user_username_max_length... OK
  Applying auth.0009_alter_user_last_name_max_length... OK
  Applying auth.0010_alter_group_name_max_length... OK
  Applying auth.0011_update_proxy_permissions... OK
  Applying auth.0012_alter_user_first_name_max_length... OK
  Applying sessions.0001_initial... OK

Create model, which dictates the database scructure.
./manage.py makemigrations main
Migrations for 'main':
  main/migrations/0001_initial.py
    - Create model ToDoList
    - Create model Item

./manage.py migrate
Operations to perform:
  Apply all migrations: admin, auth, contenttypes, main, sessions
Running migrations:
  Applying main.0001_initial... OK

## Adding Database entries from the shell...

./manage.py shell
Python 3.9.1+ (default, Feb  5 2021, 13:46:56) 
[GCC 10.2.1 20210110] on linux
Type "help", "copyright", "credits" or "license" for more information.
(InteractiveConsole)
>>> from main.models import Item, ToDoList
>>> t = ToDoList(name="My List")
>>> t.save()
>>> ToDoList.objects.all()
<QuerySet [<ToDoList: My List>]>
>>> ToDoList.objects.all()
<QuerySet [<ToDoList: My List>]>

NOTE: The "def __str__(self):" is what will allow the query to return meaningful information, with out it it would return a memory address.

>>> t.item_set.all()
<QuerySet []>
>>> t.item_set.create(text="Go to the Mall", complete=False)
<Item: Go to the Mall>
>>> t.item_set.all()
<QuerySet [<Item: Go to the Mall>]>

>>> from main.models import Item, ToDoList
>>> t = ToDoList.objects
>>> t.all()
<QuerySet [<ToDoList: My List>]>
>>> t.filter(name__startswith="My")
<QuerySet [<ToDoList: My List>]>
>>> del_object = t.get(id=1)
>>> del_object.delete()
(2, {'main.Item': 1, 'main.ToDoList': 1})
>>> t1 = ToDoList(name="First List")
>>> t1.save()
>>> t1 = ToDoList(name="Second List")
>>> t1.save()
>>> t1 = ToDoList(name="Third List")
>>> t1.save()

# Create an admin dashboard login.
./manage.py createsuperuser

## Add Database to admin dashboard.
main > admin.py > +from .models import ToDoList
main > admin.py > +admin.site.register(ToDoList)


# Network Team Django Site
[CSS](https://getbootstrap.com/docs/5.0/getting-started/introduction/ "Bootstrap v5.0 Documentation")