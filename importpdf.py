from evictions.tasks import CaseImporter
from evictions.models import Case, Court

court = Court.objects.get(friendly_court_id="05-2-32")
url = 'MDJReport.ashx?docketNumber=MJ-05232-LT-0000030-2020&dnh=uh2R0IytzNy1UOIZLjK3%2fg%3d%3d'

ci = CaseImporter(court, None, None, None)
case = Case.objects.get(id=3079)
ci.parse_docket_text(ci.parse_case(url), '0000030', existing_case=case)
