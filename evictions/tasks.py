from background_task import background
import json
import datetime as dt
import pdftotext
import requests
from io import BytesIO
from bs4 import BeautifulSoup
from decimal import Decimal, InvalidOperation
import urllib.parse
import re
from django.utils import timezone

from .models import Case, Court

class CaseDoesNotExistError(Exception):
    """Case does not exist"""
    pass

class CaseImporter():
    def __init__(self, court, ujsViewState, ujsCaptchaAnswer, ujsBDocketCookie, ujsASPCookie, ujsBRootCookie):
        self.court = court
        self.ujsViewState = ujsViewState
        self.ujsCaptchaAnswer = ujsCaptchaAnswer
        self.ujsBDocketCookie = ujsBDocketCookie
        self.ujsASPCookie = ujsASPCookie
        self.ujsBRootCookie = ujsBRootCookie

    def import_case(self, case_id):
        formatted_case_id = str(case_id).zfill(7)
        self.parse_docket_text(self.parse_case(self.fetch_case(formatted_case_id)), formatted_case_id)

    def fetch_case(self, formatted_case_id):
        headers = {
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'Upgrade-Insecure-Requests': '1',
            'Origin': 'https://ujsportal.pacourts.us',
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-User': '?1',
            'Sec-Fetch-Dest': 'document',
            'Referer': 'https://ujsportal.pacourts.us/DocketSheets/MDJ.aspx',
            'Accept-Language': 'en-US,en;q=0.9'
        }

        cookies = {
            'f5avrbbbbbbbbbbbbbbbb': self.ujsBDocketCookie,
            'f5_cspm': '1234',
            'ASP.NET_SessionId': self.ujsASPCookie,
            'f5avrbbbbbbbbbbbbbbbb': self.ujsBRootCookie
        }

        data = {
            '__EVENTTARGET': '',
            '__EVENTARGUMENT': '',
            '__LASTFOCUS': '',
            '__VIEWSTATE': self.ujsViewState,
            '__VIEWSTATEGENERATOR': '4AB257F3',
            '__SCROLLPOSITIONX': '0',
            '__SCROLLPOSITIONY': '510',
            'ctl00$ctl00$ctl00$cphMain$cphDynamicContent$ddlSearchType': 'DocketNumber',
            'ctl00$ctl00$ctl00$cphMain$cphDynamicContent$cphSearchControls$udsDocketNumber$ddlCounty': 'Allegheny',
            'ctl00$ctl00$ctl00$cphMain$cphDynamicContent$cphSearchControls$udsDocketNumber$ddlCourtOffice': self.court.court_id,
            'ctl00$ctl00$ctl00$cphMain$cphDynamicContent$cphSearchControls$udsDocketNumber$ddlDocketType': 'LT',
            'ctl00$ctl00$ctl00$cphMain$cphDynamicContent$cphSearchControls$udsDocketNumber$txtSequenceNumber': formatted_case_id,
            'ctl00$ctl00$ctl00$cphMain$cphDynamicContent$cphSearchControls$udsDocketNumber$txtYear': '2020',
            'ctl00$ctl00$ctl00$cphMain$cphDynamicContent$btnSearch': 'Search',
            'ctl00$ctl00$ctl00$ctl07$captchaAnswer': self.ujsCaptchaAnswer,
        }

        r = requests.post('https://ujsportal.pacourts.us/DocketSheets/MDJ.aspx', headers=headers, cookies=cookies, data=data)
        soup = BeautifulSoup(r.text, 'html.parser')
        links = soup.select('a[href*="MDJReport.ashx"]')
        if (len(links) > 0):
            return links[0]['href']
        else:
            raise CaseDoesNotExistError

    def parse_case(self, case_url):
        url = 'https://ujsportal.pacourts.us/DocketSheets/%s' % case_url
        r = requests.get(url, headers={ 'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36' })
        bytes = BytesIO(r.content)
        try:
            pdf = pdftotext.PDF(bytes)
        except:
            print(r.text)

        flatten = lambda l: [item for sublist in l for item in sublist]
        parse_page = lambda p: list(filter(None, flatten([ line.split("                  ") for line in p.split("\n")])))
        parsed_pdf = list(flatten(parse_page(page) for page in pdf))
        return parsed_pdf

    def parse_docket_text(self, docket_text, formatted_case_id):
        split_take_last = lambda x:x.split(" ")[-1]

        status_index = [i for i, item in enumerate(docket_text) if 'Case Status:' in item][0]
        if (docket_text[status_index].strip() == "Case Status:"):
            status = docket_text[status_index + 1].split("                 ")[-1]
        else:
            status = docket_text[status_index].split("                 ")[-1]

        claim_amount = self.format_money(split_take_last(docket_text[status_index - 1]).strip())

        file_date_index = [i for i, item in enumerate(docket_text) if 'File Date:' in item][0]
        file_date = dt.datetime.strptime(docket_text[file_date_index + 1].strip(), '%m/%d/%Y')

        parties_start_index = [i for i, item in enumerate(docket_text) if 'Landlord/Tenant Docket' in item][0]
        parties_end_index = [i for i, item in enumerate(docket_text) if 'Page 1' in item][0]
        els = [el.strip() for el in docket_text[parties_start_index + 1:parties_end_index]]
        parties = [el.strip() for el in ' '.join(els).split("v.")]

        disposition_summary_index = [i for i, item in enumerate(docket_text) if 'DISPOSITION SUMMARY' in item][0]
        participants_index = [i for i, item in enumerate(docket_text) if 'CASE PARTICIPANTS' in item][0]

        try:
            defendant_zipcode = self.parse_value(docket_text, ValueError, disposition_summary_index, [-4, -5, -6, -3], int, split_take_last)
        except ValueError:
            last_attempt = split_take_last(docket_text[participants_index + 5])
            if (last_attempt == 'PA'):
                defendant_zipcode = 0
            else:
                defendant_zipcode = int(last_attempt)

        if ('Page' in docket_text[disposition_summary_index - 1]):
            plaintiff_zip_locations = [-2, -3]
        else:
            plaintiff_zip_locations = [-1, -2, -3]

        try:
            plaintiff_zipcode = self.parse_value(docket_text, ValueError, disposition_summary_index, plaintiff_zip_locations, int, split_take_last)
        except ValueError:
            plaintiff_zipcode = int(split_take_last(docket_text[participants_index + 8]))

        if ('CALENDAR EVENTS' in ''.join(docket_text)):
            try:
                last_event_date = self.parse_value(
                    docket_text, ValueError, participants_index, [-5, -4, -3], dt.datetime.strptime,
                    lambda x:' '.join([el.strip() for el in x.split("       ")[1:3]]), '%m/%d/%Y %I:%M %p')
            except ValueError:
                try:
                    last_event_date_info = [el.strip() for el in docket_text[participants_index - 6].split("       ")[0:2]]
                    last_event_date = dt.datetime.strptime(' '.join(last_event_date_info), '%m/%d/%Y %I:%M %p')
                except ValueError:
                    end_of_page_index = [i for i, item in enumerate(docket_text) if 'MDJS 1200' in item][0]
                    last_event_date_info = [el.strip() for el in docket_text[end_of_page_index - 5].split("       ")[1:3]]
                    last_event_date = dt.datetime.strptime(' '.join(last_event_date_info), '%m/%d/%Y %I:%M %p')
        else:
            last_event_date = file_date

        disposition_date = None
        judgment_amount = 0
        monthly_rent = 0

        if (status != 'Active' and status != 'Inactive'):
            monthly_rent_index = [i for i, item in enumerate(docket_text) if 'Monthly Rent' in item]
            if (len(monthly_rent_index) > 0):
                monthly_rent = self.format_money(docket_text[monthly_rent_index[0]].split(' ')[-1])
                disposition_date = dt.datetime.strptime(docket_text[monthly_rent_index[0] - 1].split(' ')[-1], '%m/%d/%Y')

            was_transferred_index = [i for i, item in enumerate(docket_text) if 'Case Transferred' in item]
            if (len(was_transferred_index) > 0):
                disposition_date = last_event_date = dt.datetime.strptime(docket_text[was_transferred_index[0]].split(' ')[0], '%m/%d/%Y')
                status += ", transferred"

            was_withdrawn_index = [i for i, item in enumerate(docket_text) if 'Withdrawn' in item]
            if (len(was_withdrawn_index) > 0):
                disposition_date = last_event_date = dt.datetime.strptime(docket_text[was_withdrawn_index[0] + 1].strip(), '%m/%d/%Y')
                status += ", withdrawn"
            else:
                try:
                    judgment_components_index = [i for i, item in enumerate(docket_text) if 'Judgment Components' in item]
                    judgment_amount = self.parse_value(docket_text, InvalidOperation, judgment_components_index[0], [-1, -2, -3, -4, -5], self.format_money, lambda x:split_take_last(x).strip())
                except IndexError:
                    dismissed_without_prejudice_index = [i for i, item in enumerate(docket_text) if 'Dismissed Without ' in item]
                    if (len(parties[1].split(", ")) == len(dismissed_without_prejudice_index)):
                        status += ", dismissed without prejudice"
                        disposition_date = dt.datetime.strptime(docket_text[dismissed_without_prejudice_index[0]].split(" ")[0], '%m/%d/%Y')

                    end_of_page_index = [i for i, item in enumerate(docket_text) if 'MDJS 1200' in item]
                    if (disposition_date is None and len(end_of_page_index) > 1):
                        try:
                            disposition_date = self.parse_value(
                                docket_text, ValueError, end_of_page_index[0], [-1, -2, -3], dt.datetime.strptime,
                                lambda x:x.strip(), '%m/%d/%Y')
                        except ValueError:
                            civil_disposition_index = [i for i, item in enumerate(docket_text) if 'Civil Disposition Details:' in item]
                            if (len(civil_disposition_index) > 0):
                                disposition_date = self.parse_value(
                                    docket_text, ValueError, civil_disposition_index[0], [-1, -2, -3], dt.datetime.strptime,
                                    lambda x:x.strip(), '%m/%d/%Y')

            civil_disposition_index = [i for i, item in enumerate(docket_text) if 'Civil Disposition Details:' in item]
            if (disposition_date is None and len(civil_disposition_index) > 0):
                disposition_date = self.parse_value(
                    docket_text, ValueError, civil_disposition_index[0], [-1, -2, -3], dt.datetime.strptime,
                    lambda x:x.strip(), '%m/%d/%Y')

        if (disposition_date is None and 'Closed' in status):
            raise ValueError('Must have disposition date if closed')

        Case(
            court=self.court,
            claim_amount=claim_amount,
            defendant=parties[1],
            defendant_zipcode=defendant_zipcode,
            disposition_date=disposition_date,
            file_date=file_date,
            judgment_amount=judgment_amount,
            last_event_date=last_event_date,
            last_scraped_at=dt.datetime.now(tz=timezone.utc),
            monthly_rent=monthly_rent,
            plaintiff=parties[0],
            plaintiff_zipcode=plaintiff_zipcode,
            status=status,
            ujs_id=formatted_case_id
        ).save()

    def get_disposition_date(self, docket_text, formatted_case_id):
        was_withdrawn_index = [i for i, item in enumerate(docket_text) if 'Withdrawn' in item]
        if (len(was_withdrawn_index) > 0):
            return dt.datetime.strptime(docket_text[was_withdrawn_index[0] + 1].strip(), '%m/%d/%Y')

        end_of_page_index = [i for i, item in enumerate(docket_text) if 'MDJS 1200' in item]
        if (len(end_of_page_index) > 1):
            try:
                return dt.datetime.strptime(docket_text[end_of_page_index[0] - 1].strip(), '%m/%d/%Y')
            except ValueError:
                try:
                    return dt.datetime.strptime(docket_text[end_of_page_index[0] - 2].strip(), '%m/%d/%Y')
                except ValueError:
                    return dt.datetime.strptime(docket_text[end_of_page_index[0] - 3].strip(), '%m/%d/%Y')

        civil_disposition_index = [i for i, item in enumerate(docket_text) if 'Civil Disposition Details:' in item]
        if (len(civil_disposition_index) > 0):
            try:
                return dt.datetime.strptime(docket_text[civil_disposition_index[0] - 1].split(' ')[-1], '%m/%d/%Y')
            except ValueError:
                return dt.datetime.strptime(docket_text[civil_disposition_index[0] - 2].split(' ')[-1], '%m/%d/%Y')

    def format_string_array(self, arr):
        return re.sub(" +", " ", urllib.parse.unquote(''.join(arr)))

    def format_money(self, money):
        return Decimal(money[1:].replace(',', ''))

    def parse_value(self, docket_text, error_class, start, idx_ops, operation, format_text, *extra_args):
        for idx_op in list(idx_ops):
            try:
                if (extra_args):
                    return operation(format_text(docket_text[start + idx_op]), *extra_args)
                else:
                    return operation(format_text(docket_text[start + idx_op]))
            except error_class:
                continue
        raise error_class()

@background(schedule=60)
def get_new_cases(court, ujsViewState, ujsCaptchaAnswer, ujsBDocketCookie, ujsASPCookie, ujsBRootCookie):
    # Get new cases
    latest_case_id = 1
    try:
        latest_case_id = Case.objects.filter(court__id=court).latest('ujs_id').ujs_id + 1
    except:
        pass

    ci = CaseImporter(
            Court.objects.get(pk=court),
            ujsViewState, ujsCaptchaAnswer, ujsBDocketCookie, ujsASPCookie, ujsBRootCookie
            )

    while(True):
        try:
            ci.import_case(latest_case_id)
            latest_case_id += 1
        except CaseDoesNotExistError:
            latest_case_id += 1
            try:
                print(latest_case_id)
                ci.import_case(latest_case_id)
                latest_case_id += 1
            except CaseDoesNotExistError:
                print("CaseDoesNotExist!! %s" % latest_case_id)
                break

    # TODO: Update cases that are not closed
    # cases = Case.objects.filter(court__id=court).exclude(status__contains="Closed")
