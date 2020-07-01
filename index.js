const cheerio = require('cheerio');
const PDFParser = require('pdf2json');
const request = require('request-promise');
const { unescape } = require('querystring');

ujsFormData = global.ujsFormData = {
  ujsViewState: '125d7131-73a1-4271-804e-d646fef08f4b',
  ujsCaptchaAnswer: '-845263735',
  BDocketSheet: 'BJIIJKBBFPDIIEEFEHBCDGNECFKMAPNLJPNLEBIKCEEBJDLPDMDEBPKHMGGFOADFKEKDHFOMPHJCDBNAHOHAKOOMEMGBEKPOJOKNPCIBGMCPPNBGDDAECLMPBCEPCHJD',
  ASPRoot: 'c4gcinmbrlzrvjrftrirksl3',
  BRoot: 'EHBGFIEECHFHDEMFDCOAGEJEAPOCNIIHGPBPJPGGINAOCPNNEGCLHOMMMAAIMDDNILCDMIGOMOKNMCEIEBCAPHMPJNNBDFECBKFLJLBBICPKBMFKCNDJMPGJAGBMKFLN',
};

const getCaseLink = (serializedCourtId, serializedCaseNumber) => {
  return request({
    url: 'https://ujsportal.pacourts.us/DocketSheets/MDJ.aspx',
    method: 'POST',
    headers: {
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
      'Accept-Language': 'en-US,en;q=0.9',
      'Cookie': `f5avrbbbbbbbbbbbbbbbb=${ujsFormData.BDocketSheet}; f5_cspm=1234; ASP.NET_SessionId=${ujsFormData.ASPRoot}; f5avrbbbbbbbbbbbbbbbb=${ujsFormData.BRoot}`,
    },
    form: {
      '__EVENTTARGET': '',
      '__EVENTARGUMENT': '',
      '__LASTFOCUS': '',
      '__VIEWSTATE': ujsFormData.ujsViewState,
      '__VIEWSTATEGENERATOR': '4AB257F3',
      '__SCROLLPOSITIONX': '0',
      '__SCROLLPOSITIONY': '510',
      'ctl00$ctl00$ctl00$cphMain$cphDynamicContent$ddlSearchType': 'DocketNumber',
      'ctl00$ctl00$ctl00$cphMain$cphDynamicContent$cphSearchControls$udsDocketNumber$ddlCounty': 'Allegheny',
      'ctl00$ctl00$ctl00$cphMain$cphDynamicContent$cphSearchControls$udsDocketNumber$ddlCourtOffice': serializedCourtId,
      'ctl00$ctl00$ctl00$cphMain$cphDynamicContent$cphSearchControls$udsDocketNumber$ddlDocketType': 'LT',
      'ctl00$ctl00$ctl00$cphMain$cphDynamicContent$cphSearchControls$udsDocketNumber$txtSequenceNumber': serializedCaseNumber,
      'ctl00$ctl00$ctl00$cphMain$cphDynamicContent$cphSearchControls$udsDocketNumber$txtYear': '2020',
      'ctl00$ctl00$ctl00$cphMain$cphDynamicContent$btnSearch': 'Search',
      'ctl00$ctl00$ctl00$ctl07$captchaAnswer': ujsFormData.ujsCaptchaAnswer,
    },
  })
  .then((body) => {
    const $ = cheerio.load(body);
    const links = $('a[href*="MDJReport.ashx"]');
    if (links.length > 0) {
      return Promise.resolve({
        serializedCourtId,
        serializedCaseNumber,
        url: links[0].attribs.href
      });
    }

    return Promise.reject(new Error("Can't find docket sheet link"));
  })
  .catch((e) => {
    throw e;
  });
};

const createCaseRecord = (caseLink) => { return caseLink; };

const getCaseFile = (caseRecord) => {
  return request({
    url: `https://ujsportal.pacourts.us/DocketSheets/${caseRecord.url}`,
    method: 'GET',
    encoding: null,
  })
  .then((resBody) => {
    return new Promise((resolve, reject) => {
      const parser = new PDFParser();
      parser.on('pdfParser_dataError', reject);
      parser.on('pdfParser_dataReady', ({ formImage }) => {
        resolve(formImage.Pages.map((p) => p.Texts).flat().map((t) => t.R).flat().map((r) => r.T));
      });
      parser.parseBuffer(resBody);
    });
  })
  .then((docketText) => {
    return Promise.resolve({ ...caseRecord, docketText });
  });
};

const parseCaseRecord = (caseFile) => {
  const { docketText } = caseFile;
  const formatStringArray = (arr) => unescape(arr.join('')).replace(/ {1,}/g, " ");

  require('fs').writeFileSync(`${caseFile.serializedCaseNumber}.json`, JSON.stringify(docketText));

  const pageIndex = docketText.indexOf('CASE%20INFORM') - 1;
  const offset = pageIndex - 9;

  let extraOffset = 0;
  if (docketText[22 + offset].includes('.')) {
    extraOffset = 1;
  }

  const dispositionSummaryIndex = docketText.findIndex((el) => el === 'DISPOSITION%20SUMMA');
  const defendantZipcode = formatStringArray(docketText.slice(dispositionSummaryIndex - 1, dispositionSummaryIndex)).split(" ")[1];

  const plaintiffIndex = docketText.findIndex((el) => el === 'Plainti');
  const plaintiffZipcode = formatStringArray(docketText.slice(plaintiffIndex - 1, plaintiffIndex)).split(" ")[1];

  const participantsIndex = docketText.findIndex((el) => el === 'PARTICIPANTS');
  const lastEventDate = new Date(Date.parse(
    `${formatStringArray(docketText.slice(participantsIndex - 6, participantsIndex - 5))} 
    ${formatStringArray(docketText.slice(participantsIndex - 5, participantsIndex - 4))}`
  ));

  // Closed case information
  let dispositionDate = '';
  let judgmentAmount = '';
  let monthlyRent = '';
  const status = docketText[19 + offset];
  if (status !== 'Active') {
    const monthlyRentIndex = docketText.findIndex((el) => el === 'Monthly%20Rent%3A');
    if (monthlyRentIndex !== -1) {
      monthlyRent = formatStringArray(docketText.slice(monthlyRentIndex + 1, monthlyRentIndex + 2));
      dispositionDate = formatStringArray(docketText.slice(monthlyRentIndex - 1, monthlyRentIndex));
    }

    const wasWithdrawnIndex = docketText.findIndex((el) => el === 'Withdrawn');
    if (wasWithdrawnIndex !== -1) {
      dispositionDate = formatStringArray(docketText.slice(wasWithdrawnIndex + 1, wasWithdrawnIndex + 2));
    } else {
      judgmentAmount = formatStringArray(docketText.slice(25 + offset + extraOffset, 25 + offset + extraOffset + 1));
    }
  }

  const parties = formatStringArray(docketText.slice(docketText.indexOf('Tenant%20Docket') + 1, pageIndex)).split(' v. ');

  return Promise.resolve({
    ... {
    claimAmount: formatStringArray(docketText.slice(21 + offset + extraOffset, 21 + offset + extraOffset + 1)),
    defendant: parties[1],
    defendantZipcode,
    dispositionDate,
    fileDate: formatStringArray(docketText.slice(12 + offset, 12 + offset + 1)),
    judgmentAmount,
    lastEventDate: lastEventDate.toLocaleString(),
    monthlyRent,
    plaintiff: parties[0],
    plaintiffZipcode,
    status,
  }, ...caseFile });
};

const updateCaseRecord = (caseFile) => {
  //console.log(caseFile);
};

parseCaseRecord({ docketText: require('./0000002.json') }).then(updateCaseRecord);

const fetchNextCase = (judge, lastCaseId) => {
  console.log('GETTING ', judge, lastCaseId + 1);
  const nextCaseId = String(lastCaseId + 1).padStart(7, '0');

  return getCaseLink(judge, nextCaseId)
  .then(createCaseRecord)
  .then(getCaseFile)
  .then(parseCaseRecord)
  .then(updateCaseRecord)
  .then(fetchNextCase.bind(null, judge, lastCaseId + 1))
  .catch(console.log);
};

const judges = ['5203'];
const lastCaseId = 2;
judges.forEach((judge) => fetchNextCase(judge, lastCaseId));
