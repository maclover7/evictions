from django.db import models

# Create your models here.

class Court(models.Model):
    friendly_court_id = models.CharField(max_length=200)
    court_id = models.CharField(max_length=200)
    judge_name = models.CharField(max_length=200)

    def __str__(self):
        return self.friendly_court_id
