from django.db import models

class Court(models.Model):
    friendly_court_id = models.CharField(max_length=200)
    court_id = models.CharField(max_length=200)
    judge_name = models.CharField(max_length=200)

    def __str__(self):
        return self.friendly_court_id

class Case(models.Model):
    court = models.ForeignKey(Court, on_delete=models.CASCADE)
    claim_amount = models.DecimalField(max_digits=12, decimal_places=2)
    defendant = models.TextField()
    defendant_zipcode = models.IntegerField()
    disposition_date = models.DateField(null=True, blank=True)
    file_date = models.DateField()
    judgment_amount = models.DecimalField(max_digits=12, decimal_places=2)
    last_event_date = models.DateField()
    last_scraped_at = models.DateTimeField()
    monthly_rent = models.DecimalField(max_digits=12, decimal_places=2)
    plaintiff = models.TextField()
    plaintiff_zipcode = models.IntegerField()
    status = models.TextField()
    ujs_id = models.IntegerField()
