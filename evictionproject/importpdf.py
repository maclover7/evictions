from evictions.tasks import CaseImporter
from evictions.models import Case, Court

# court = Court.objects.filter(friendly_court_id="05-2-47")[0]
# url = 'MDJReport.ashx?docketNumber=MJ-05247-LT-0000072-2020&dnh=ZrLfO13YsmrjUdv6J4GL3g%3d%3d'
# ci = CaseImporter(court, None, None, None, None, None)
# ci.parse_docket_text(ci.parse_case(url), '0000072')

### START: 314 -> 196 -> 84 -> 78

object_id_list = [
        4288, 4300, 4376, 4419, 4486, 4538, 4559, 4561, 4669, 4709, 4743, 4919,
        4925, 4926, 4927, 4928, 4937, 4939, 5112, 5191, 5243, 5244, 5254, 5368,
 5268,
 5278,
 5290,
 5291,
 5292,
 5294,
 5295,
 5296,
 5297,
 5298,
 5311,
 5313,
 5314,
 5328,
 5332,
 5333,
 5334,
 5337,
 5338,
 5340,
 5341,
 5384,
 5399,
 5400,
 5401,
 5406,
 5407,
 5411,
 5414,
 5418,
 5419,
 5423,
 5427,
]
cases = Case.objects.filter(disposition_date__isnull=True).filter(status__contains='Closed').exclude(id__in=object_id_list)[0:20]
# cases = Case.objects.filter(id=4213)
for eviction_case in cases:
    ci = CaseImporter(eviction_case.court,
        'c2d9f82e-30ae-410b-921b-bb0f3fe34909',
        '496414179',
        'LGJKNCINDMMKAELCCMKCNPOEALMGFJJOONEINAMAMAGMKGIJLEEIMIMOEBNLJIEIIPIDLMCODMKGJJJOKPIAFAFFDHMEBBPCBPKOPGOMHEIBLAFALDPHLMFANDMHLBOL',
        'c4gcinmbrlzrvjrftrirksl3',
        'DDLCPCMDFBHCKOKLCPEHAHBLEKIABJELGGMDKJKNALANECPDPPPIDLFMNFLBBNHCPLADGMOLOHPIBBBEDIBAGGGKKIKHLHONOPOJJIGJEGGIIFLBONACJGPGMKINHAAE')

    formatted_case_id = str(eviction_case.ujs_id).zfill(7)
    try:
        new_dd = ci.get_disposition_date(ci.parse_case(ci.fetch_case(formatted_case_id)), formatted_case_id)
        if (new_dd is not None):
            eviction_case.disposition_date = new_dd
            eviction_case.save()
        else:
            print(new_dd)
            print('Error %s' % eviction_case.id)
    except:
        print('Error %s' % eviction_case.id)

# Do a query of closed cases with no disposition dates, and update them all
# from evictions.models import Case
# Case.objects.filter(disposition_date__isnull=True).filter(status__contains='Closed')
