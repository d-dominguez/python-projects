import requests
import xmltodict as xm
import pandas as pd
import numpy as np
import itertools as it
import ast
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

# '**** ENTER YOUR USER ID ****' & '**** ENTER YOUR GOOGLE API KEY ****' must be replaced first.

def getInput():
    user_input = input('Please enter zip code:\n')
    user_input2 = input('Please re-enter zip code:\n')
    if ((len(user_input) is not 5)):
        print('\n***PLEASE CHECK THE ZIP CODE!!*** Input must be 5 digits long.',
              'Your input was ',len(user_input),' characters long!!')
    elif ((user_input.isdigit()&user_input2.isdigit())is not True):
        print('\n***PLEASE CHECK THE ZIP CODE!!*** Input must be numeric!! Your inputs were: ',
             user_input,' & ',user_input2)
    elif (user_input != user_input2):
        print('\nTHE ZIP CODES DO NOT MATCH!!')
    else:
        print('\n==================================\n\n',
              '\nProcessing.....',
              '\n...............',
              '\n...............',
              '\n...............',
              '\n...............',
              '\n...............',
              '\n...............',
              '\n...............')
    return user_input

def validateZip(zip):
    payload="http://production.shippingapis.com/ShippingAPI.dll?API=CityStateLookup&XML=<CityStateLookupRequest USERID='**** ENTER YOUR USER ID ****'><ZipCode ID='0'><Zip5>"+zip+"</Zip5></ZipCode></CityStateLookupRequest>"
    r = requests.get(payload)
    response = xm.parse(r.text)
    city = response['CityStateLookupResponse']['ZipCode']['City']
    state = response['CityStateLookupResponse']['ZipCode']['State']
    city.strip()
    state.strip()
    print('Zip Code '+zip+' is located in '+city+', '+state)
    return city + ', ' + state

def getCounty(zip):
    payload = ''.join(["https://maps.googleapis.com/maps/api/geocode/xml?address=",
                       user_input,
                       "'**** ENTER YOUR GOOGLE API KEY ****'"])
    r = requests.get(payload)
    response = xm.parse(r.text)
    county = response['GeocodeResponse']['result']['address_component'][2]['long_name']
    state_s = response['GeocodeResponse']['result']['address_component'][3]['short_name']
    state_l = response['GeocodeResponse']['result']['address_component'][3]['long_name']
    county = county.replace(' County','')
    county = str(county + ', ' + state_s)
    return {'county':county, 'state_s':state_s ,'state_l':state_l }

def getStateCountyCodes(dictionary):
    codes = pd.read_csv('https://lehd.ces.census.gov/data/schema/latest/label_geography.csv')
    county = dictionary['county']
    state = dictionary['state_l']
    state_code = codes.geography[(codes.geo_level == 'S')&(codes.label == state)].iloc[0]
    county_code = codes.geography[(codes.geo_level == 'C')&(codes.label == county)].iloc[0]
    county_code = county_code[2:]
    return {'state_code':state_code, 'county_code':county_code}

def getCensusData(dict1):
    state_code = str(dict1['state_code'])
    county_code = str(dict1['county_code'])
    payload = ''.join(["https://api.census.gov/data/timeseries/healthins/sahie?get=IPRCAT,NIC_PT,NUI_PT&for=county:",
                       county_code,
                       "&in=state:",
                       state_code,
                       "&time=2016"])
    r = requests.get(payload)
    response = r.text
    response = response.replace('\n','')
    response =  ast.literal_eval(response)
    df = pd.Series(response)
    df = pd.DataFrame(df, columns = ["data"])
    df = pd.DataFrame(df.data.values.tolist()).add_prefix('__')
    new_header = df.iloc[0] #grab the first row for the header
    df = df[1:] #take the data less the header row
    df.columns = new_header #set the header row as the df header
    df.iloc[:,1:6] = df.iloc[:,1:6].apply(pd.to_numeric)
    df.columns = ['Income-to-Poverty Ratio Group','Insured', 'Uninsured','Year','State Code', 'County Code']
    df['Uninsured %'] = df['Uninsured']/(df['Insured']+df['Uninsured'])
    return df

def generateBarChart_total(df):
    bar_width=0.45
    opacity = 0.4

    plt.xlabel('')
    plt.ylabel('Total in Millions')

    mx = max(df['Insured'])*1.3
    mx = int(mx)

    values = np.arange(0,mx,200000)
    value_increment = 1
    bar1 = plt.bar(np.arange(len(df['Uninsured']))+ bar_width, df['Uninsured'], bar_width, align='center', alpha=opacity, color='r', label='Uninsured')
    bar2 = plt.bar(range(len(df['Insured'])), df['Insured'], bar_width, align='center', alpha=opacity, color='g', label='Insured')

    plt.yticks(values * value_increment, ['%s' % round(val,0) for val in values])
    plt.xticks(range(len(df['Income-to-Poverty Ratio Group'])),('Group\n1', 'Group\n2', 'Group\n3', 'Group\n4', 'Group\n5','Group\n6'))

    for rect in bar1 + bar2:
        height = rect.get_height()
        plt.text(rect.get_x() + rect.get_width()/2.0, height, '%s' % int(height), ha='center', va='bottom')

    plt.legend()
    fig_size = plt.rcParams["figure.figsize"]
    fig_size[0] = 12
    fig_size[1] = 8
    plt.rcParams["figure.figsize"] = fig_size
    plt.show()

def generateBarChart_percent(df):  
        bar_width=0.45
        opacity = 0.4

        plt.xlabel('')
        plt.ylabel('% Uninsured')

        mx = (max(df['Uninsured %']))*1.3

        values = np.arange(0.0,mx,.01)*100
        value_increment = .10
        bar1 = plt.bar(np.arange(len(df['Uninsured %']*100))+ bar_width, df['Uninsured %']*100, bar_width, align='center', alpha=opacity, color='r', label='Uninsured %')


        plt.yticks(values, ['%s' % round(val,2) for val in values])
        plt.xticks(range(len(df['Income-to-Poverty Ratio Group'])),('Group\n1', 'Group\n2', 'Group\n3', 'Group\n4', 'Group\n5','Group\n6'))

        for rect in bar1:
            height = round(rect.get_height(),2)
            plt.text(rect.get_x() + rect.get_width()/2, height, '%s' % height, ha='center', va='bottom')

        plt.legend()
        fig_size = plt.rcParams["figure.figsize"]
        fig_size[0] = 12
        fig_size[1] = 8
        plt.rcParams["figure.figsize"] = fig_size
        plt.show()
  
user_input = getInput()
city_state = validateZip(user_input)
county_results = getCounty(user_input)
codes = getStateCountyCodes(county_results)
insurance_data = getCensusData(codes)
generateBarChart_total(insurance_data)
enerateBarChart_percent(insurance_data)

