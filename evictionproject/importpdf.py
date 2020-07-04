from evictions.tasks import CaseImporter
from evictions.models import Court

court = Court.objects.filter(friendly_court_id="05-2-07")[0]

url = 'MDJReport.ashx?docketNumber=MJ-05207-LT-0000106-2020&dnh=11vpXRQ5ulR1wgw7buLrNA%3d%3d'

ci = CaseImporter(court, None, None, None, None, None)
ci.parse_docket_text(ci.parse_case(url), '0000106')
