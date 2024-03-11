# welcome to dm_assistant
A Dungeon Master Assistant App
# install virtualenv
mkvirtualenv dm_assistant_django
cd dm_assistant
# install requirements
pip install -r requirements.txt
# run migrations
python manage.py migrate
# create superuser, so you can login locally
python maange.py createsuperuser
# run server
python manage.py runserver
# notes about index
The index will only be regenerated if the storage folder and its contents are not present.