import pandas as pd
from bs4 import BeautifulSoup
import requests
import re
import datetime
import dateutil

def check_pattern(input_string):
    gold_pattern = re.compile('^.*?www.goodreturns.in.*?$')
    mutual_fund_pattern = re.compile('^.*?/mutual-funds/.*?$')
    insurance_pattern = re.compile('^.*?/insurance/.*?$')
    if bool(gold_pattern.match(input_string)):
        return 'Gold'
    elif bool(mutual_fund_pattern.match(input_string)):
        return 'MF'
    elif bool(insurance_pattern.match(input_string)):
        return 'Insurance'
    else:
        return 'Unknown'

def request_data(url,type):
    if type == 'Gold':
        headers = {'Host': 'www.goodreturns.in',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:105.0) Gecko/20100101 Firefox/105.0'}
        htmlData = requests.get(url,headers=headers)
    else:
        htmlData = requests.get(url)
    return BeautifulSoup(str(htmlData.content), "html.parser")

def add_entry(input_dict,name,url,date,nav):
    input_dict['MF Scheme'].append(name)
    input_dict['URL'].append(url)
    input_dict['Date'].append(date)
    input_dict['NAV'].append(nav)

def date_clean(date,type):
    if type == 'MF':
        date = re.findall("^\(as on (.*?)\)",date)[0]
    else:
        date = re.findall("^NAV as on (.*?)$",date)[0]
    return dateutil.parser.parse(date).strftime("%d-%m-%Y")

def main():
    input_dataframe = pd.read_excel('nav-automation-input-data.xlsx')
    mfscheme_column = input_dataframe['MF Scheme']
    url_column = input_dataframe['URL']
    test_dict = dict(zip(mfscheme_column,url_column))
    output_columns = ['MF Scheme','URL','Date','NAV']
    output_dataframe = pd.DataFrame(columns = output_columns)
    row_data = {'MF Scheme':[],'URL':[],'Date':[],'NAV':[]}
    for name,url in test_dict.items():
        type = check_pattern(url)
        soup = request_data(url,type)
        if type == 'MF':
            nav_value = soup.find("span", {"class": "amt"}).text
            date = date_clean(soup.find("div", {"class": "grayvalue"}).text,type)
        elif type == 'Insurance':
            nav_value = '₹ '+soup.find_all("div",{"class":re.compile("FL PR8 (rD|gR)_30")})[0].find('strong').text
            date = date_clean(soup.find_all("div",{"class":"CL gL_12"})[0].text,type)
        elif type == 'Gold':
            nav_value_raw = soup.find_all('strong',{'id':'el'})[0].text
            nav_value = re.findall('^.*?(₹ [0-9\,]+).*?$',nav_value_raw)[0]
            date = datetime.date.today().strftime("%d-%m-%Y")
        else:
            print("Match failed, contact programmer about ",url)
            nav_value = 0
            date = 'None'
        print(name,date,nav_value)
        add_entry(row_data,name,url,date,nav_value)

    output_dataframe = pd.concat([output_dataframe,pd.DataFrame(row_data)],ignore_index=True)
    output_dataframe.reset_index()
    output_dataframe.to_excel("output.xlsx",sheet_name="Processed",index=False)

main()
    
