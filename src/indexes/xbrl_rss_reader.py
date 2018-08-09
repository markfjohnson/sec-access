import feedparser
import os.path
import sys, getopt
import time, datetime
import json
import socket
from io import BytesIO
from zipfile import ZipFile
from urllib.request import urlopen
from bs4 import BeautifulSoup
import re
from pyspark import SparkConf, SparkContext
from pyspark.sql.types import *
from pyspark.sql import SQLContext,Row, SparkSession
from pyspark.sql.functions import udf
from pyspark.sql.functions import to_timestamp, to_date
from pyspark.sql.types import DateType

sc = SparkContext("local","simple App")
sqlContext = SQLContext(sc)
spark = SparkSession(sc)

def get_xbrl_element_value(tag, parser):
    h = parser.find(re.compile(tag,re.IGNORECASE | re.MULTILINE)).text
    return(h)

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        pass

    try:
        import unicodedata
        unicodedata.numeric(s)
        return True
    except (TypeError, ValueError):
        pass
    return False

def parse_filing(a):
    soup = BeautifulSoup(a, 'lxml')
    document_type = get_xbrl_element_value("dei:DocumentType",soup)
    company_name = get_xbrl_element_value("dei:EntityRegistrantName",soup)
    symbol = get_xbrl_element_value("dei:TradingSymbol",soup)
    amendment_flag = get_xbrl_element_value("dei:AmendmentFlag",soup)
    fiscal_year = get_xbrl_element_value("dei:DocumentFiscalYearFocus",soup)
    period_end = get_xbrl_element_value("DocumentPeriodEndDat",soup)
    context_info = soup.find_all(re.compile('^(context|xbrli:context)', re.IGNORECASE | re.MULTILINE))
    custom_data = soup.find_all(re.compile('^((?!(us-gaap|dei|xbrll|xbrldi)).)*:\s*', re.IGNORECASE | re.MULTILINE))
    hdr = {'doc_type': document_type, 'company_name':company_name, 'symbol':symbol, 'amendment_flag':amendment_flag, 'fiscal_year':fiscal_year, 'period_end':period_end,'custom_data':custom_data, 'context_info':context_info}
    return hdr



def excluded_xbrl_files(fname):
    if (fname.endswith("xsd") or fname.endswith("_cal.xml") or fname.endswith("_def.xml") or fname.endswith("_lab.xml") or fname.endswith("_pre.xml")):
        return False
    else:
        return True


def access_xbrl_doc_data(link):
    resp = urlopen(link)
    zip_ref = ZipFile(BytesIO(resp.read()))
    fileList = zip_ref.namelist()
    xbrl_file = [x for x in fileList if excluded_xbrl_files(x)][0]
    a = zip_ref.read(xbrl_file)

    return(a)

def extract_xbrl(doc_values):
    custom_data = doc_values['custom_data']
    result = []
    for data in custom_data:
        context_id = data.attrs.get('contextref')
        if (context_id != None):
            context_info = [ctx for ctx in doc_values['context_info'] if ctx['id']==context_id]
            period_date = context_info[0].contents[3].contents[1].text
            a = data.attrs.get('decimals')

            if (a != None and a != 'INF'):
                positions = len(data.text) - abs(int(a))
                if (positions <= 0):
                    value = float(data.text)
                else:
                    if (data.text.find(".") == -1):
                        value = float(data.text[:positions] + '.' + data.text[positions:])
                    else:
                        value = float(data.text)
            else:
                if (len(data.text) > 0):
                    if (is_number(data.text)):
                        value = float(data.text)
                    else:
                        value = data.text
                else:
                    value = 0


            r = Row(company_name=doc_values['company_name'], doc_type=doc_values['doc_type'],
                fiscal_year=doc_values['fiscal_year'], period_date=period_date, period_end=doc_values['period_end'],
                symbol=doc_values['symbol'],amendment_flag=doc_values['amendment_flag'], xbrl=data.name, value=value)

            result.append(r)


#            print(doc_values['company_name'], doc_values['doc_type'], doc_values['fiscal_year'], period_date,
#                  doc_values['period_end'], doc_values['symbol'], doc_values['amendment_flag'], data.name, value)
#            print("----------------------------------------------")

    return(result)




def SECdownload_rss_entries(year, month):
    edgarFilingsFeed = 'http://www.sec.gov/Archives/edgar/monthly/xbrlrss-' + str(year) + '-' + str(month).zfill(
        2) + '.xml'
    print(edgarFilingsFeed)
    feed = feedparser.parse(edgarFilingsFeed).entries
    return(feed)

def convert_entries(entry_json):
    filing_date = time.strptime(entry_json['edgar_filingdate'],"%m/%d/%Y")
#    period_date = time.strptime(entry_json.get('edgar_period'), "%Y%m%d")

    statement = (entry_json['edgar_companyname'],
                 entry_json['edgar_formtype'],
                 entry_json['edgar_filingdate'],
                 entry_json['edgar_ciknumber'],
                 entry_json.get('edgar_period'),
                 entry_json['id'])
    return(statement)
def collect_filings(filing):
    xbrl_document = access_xbrl_doc_data(filing)
    doc_values = parse_filing(xbrl_document)
    filing = extract_xbrl(doc_values)

def build_index_table(base_entries):
    schema = StructType([StructField('companyname', StringType()),
                         StructField('formtype', StringType()),
                         StructField('filingdate', StringType()),
                         StructField('cik', StringType()),
                         StructField('period', StringType()),
                         StructField('id', StringType())])
    sec_entry_df = spark.createDataFrame(base_entries, schema)
    sec_entry_df = sec_entry_df.withColumn("filingdate", to_date("filingdate", "MM/dd/yyyy"))
    sec_entry_df = sec_entry_df.withColumn('period', to_date("period", "yyyyMMdd"))
    return(sec_entry_df)

#
#--------------------------------------------------------------------------------------
# main - Program entry point
#--------------------------------------------------------------------------------------
def main(argv):
    year = 2013
    month = 1
    from_year = 1999
    to_year = 1999
    year_range = False
    if not os.path.exists("sec"):
        os.makedirs("sec")

    socket.setdefaulttimeout(10)
    start_time = time.time()
    try:
        opts, args = getopt.getopt(argv, "hy:m:f:t:", ["year=", "month=", "from=", "to="])
    except getopt.GetoptError:
        print('loadSECfilings -y <year> -m <month> | -f <from_year> -t <to_year>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('loadSECfilings -y <year> -m <month> | -f <from_year> -t <to_year>')
            sys.exit()
        elif opt in ("-y", "--year"):
            year = int(arg)
        elif opt in ("-m", "--month"):
            month = int(arg)
        elif opt in ("-f", "--from"):
            from_year = int(arg)
            year_range = True
        elif opt in ("-t", "--to"):
            to_year = int(arg)
            year_range = True

    if year_range:
        if from_year == 1999:
            from_year = to_year
        if to_year == 1999:
            to_year = from_year
        index_range = []
        for year in range(from_year, to_year + 1):
            for month in range(1, 12 + 1):
                index_range.append((year,month))
        index_dates = sc.parallelize(index_range,4)

        base_entries = index_dates.flatMap(lambda rss: SECdownload_rss_entries(rss[0],rss[1])).map(lambda rss: convert_entries(rss))
        xbrl_df = build_index_table(base_entries)
        a = xbrl_df.rdd.flatMap(lambda filing: collect_filings(filing.id))
        df = a.toDF()
        print(df.show(5000))

    end_time = time.time()
    print("Elapsed time:", end_time - start_time, "seconds")



if __name__ == "__main__":
    main(sys.argv[1:])
