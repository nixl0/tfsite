from django.db import models
from django.contrib.auth.models import User

class PersonalizedUser(models.Model):
    user = models.OneToOneField(User, models.CASCADE)
    interests = models.CharField(max_length=6000)

class Post(models.Model):
    tags = models.CharField(max_length=1000, blank=True)
    desc = models.CharField(max_length=5000, blank=True)
    image = models.ImageField(upload_to='images/')
    highlights = models.CharField(max_length=400)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)

class Like(models.Model):
    post = models.ForeignKey(Post, on_delete=models.SET_DEFAULT, default=1)
    author = models.ForeignKey(User, on_delete=models.SET_DEFAULT, default=1)

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.SET_DEFAULT, default=1)
    author = models.ForeignKey(User, on_delete=models.SET_DEFAULT, default=1)
    body = models.CharField(max_length=10000)
    timestamp = models.DateTimeField()