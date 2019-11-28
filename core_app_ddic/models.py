from django.db import models
from django.contrib.auth.models import User


# class Post(models.Model):
#     post = models.BooleanField()
#     user = models.ForeignKey(User)
#     date = models.DateTimefield


class Todo(models.Model):
    title = models.CharField(max_length=200)
    # text = models.TextField()
    completed = models.BooleanField(null=False,default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.title   #this makes djangoadmin page show title inthe list