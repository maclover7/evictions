from evictions.models import Case

relevant_cases1 = Case.objects.filter(status__contains='Inactive').all()
relevant_cases2 = Case.objects.filter(status__contains='Active').all()
# > 862 of 2370
print('rcs', relevant_cases1.count() + relevant_cases2.count())

print('nc', Case.objects.exclude(status__contains="Closed").all().count())
print('hi')

print('c_no_dd', Case.objects.filter(status__contains='Inactive', disposition_date=None).all()[0])
