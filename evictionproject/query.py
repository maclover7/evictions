from evictions.models import Case
from django.db.models import F

relevant_cases = Case.objects.filter(status__contains='Closed').exclude(last_event_date=F('disposition_date')).all()
print(relevant_cases.count())
# > 862 of 2370

relevant_cases.update(last_event_date=F('disposition_date'))

relevant_cases = Case.objects.filter(status__contains='Closed').exclude(last_event_date=F('disposition_date')).all()
print(relevant_cases.count())
# > 0
