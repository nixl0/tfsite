from django_seed import Seed

seeder = Seed.seeder()

from models import User, PersonalizedUser, Post
seeder.add_entity(User, 5)