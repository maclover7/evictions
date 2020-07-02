import logging
import json
import datetime as dt

from evictions.models import Case, Court

c = Court.objects.get(friendly_court_id='05-2-03')

lastCaseId = 1
while (lastCaseId < 44):
    fancy_id = str(lastCaseId).zfill(7)
    f = open('../%s.json' % fancy_id,)
    docketText = json.load(f)

    def format_string_array(arr):
        import urllib.parse
        import re
        return re.sub(" +", " ", urllib.parse.unquote(''.join(arr)))

    def format_money(money):
        from decimal import Decimal
        import re
        return Decimal(money[1:].replace(',', ''))

    ### DO THE THING!
    page_index = docketText.index('CASE%20INFORM') - 1
    offset = page_index - 9

    extra_offset = 0
    if ('.' in docketText[22 + offset]):
        extra_offset = 1

    claim_amount = format_money(format_string_array([docketText[21 + offset + extra_offset]]))

    file_date_index = docketText.index('File%20Date%3A')
    file_date = dt.datetime.strptime(format_string_array(''.join(docketText[page_index + 3:file_date_index])), '%m/%d/%Y')

    disposition_summary_index = docketText.index('DISPOSITION%20SUMMA')
    defendant_zipcode = format_string_array([docketText[disposition_summary_index - 1]]).split(" ")[-1]

    plaintiff_index = docketText.index('Plainti')
    plaintiff_zipcode = format_string_array(arr=docketText[plaintiff_index - 1]).split(" ")[-1]

    participants_index = docketText.index('PARTICIPANTS')

    last_event_date_start_index = participants_index - 6
    if(any(i.isdigit() for i in docketText[participants_index - 7])):
        last_event_date_start_index = participants_index - 7

    last_event_date = dt.datetime.strptime(
            ' '.join([format_string_array(
                ' '.join(
                    [''.join(docketText[last_event_date_start_index:participants_index - 5]),
                    docketText[participants_index - 5]
                    ])
                )]),
            '%m/%d/%Y %I:%M %p')

    disposition_date = None
    judgment_amount = 0
    monthly_rent = 0

    status = docketText[19 + offset]
    if (status != 'Active'):
        try:
            monthly_rent_index = docketText.index('Monthly%20Rent%3A')
            monthly_rent = format_money(format_string_array([docketText[monthly_rent_index + 1]]))
            disposition_date = dt.datetime.strptime(format_string_array([docketText[monthly_rent_index - 1]]), '%m/%d/%Y')
        except ValueError:
            pass

        try:
            was_withdrawn_index = docketText.index('Withdrawn')
            disposition_date = dt.datetime.strptime(format_string_array([docketText[was_withdrawn_index + 1]]), '%m/%d/%Y')
        except ValueError:
            pass
            # TODO: Make below line work again
            # judgment_amount = format_money(format_string_array([docketText[25 + offset + extra_offset]]))

    parties = format_string_array(docketText[docketText.index('Tenant%20Docket') + 1:page_index]).split(' v. ')

    Case(
        court=c,
        claim_amount=claim_amount,
        defendant=parties[1],
        defendant_zipcode=int(defendant_zipcode),
        disposition_date=disposition_date,
        file_date=file_date,
        judgment_amount=judgment_amount,
        last_event_date=last_event_date,
        monthly_rent=monthly_rent,
        plaintiff=parties[0],
        plaintiff_zipcode=int(plaintiff_zipcode),
        status=status,
        ujs_id=fancy_id
    ).save()

    lastCaseId = lastCaseId + 1
