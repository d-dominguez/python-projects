import requests
import math
import xmltodict as xm
import pandas as pd
import numpy as np
import ast
import matplotlib.pyplot as plt

# Function asks the user to input a zip code and checks that the input is
# numeric and exactly 5 digits
def getInput():
    user_input = input('Please enter zip code:\n>>>> ')
    user_input2 = input('Please re-enter zip code:\n>>>> ')
    if ((len(user_input) is not 5)):
        print('\n***PLEASE CHECK THE ZIP CODE!!*** Input must be 5 digits long.',
              'Your input was ', len(user_input),' characters long!!')
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


# Function takes zip code returnd by getInput() and checks if zip code is valid and returns the city
# and state associated with the zip code using the USPS API
def validateZip(zip):
    payload = "http://production.shippingapis.com/ShippingAPI.dll?API=CityStateLookup&XML=<CityStateLookupRequest USERID='**** ENTER YOUR USER ID ****'><ZipCode ID='0'><Zip5>" + zip + "</Zip5></ZipCode></CityStateLookupRequest>"
    r = requests.get(payload)
    response = xm.parse(r.text)
    city = response['CityStateLookupResponse']['ZipCode']['City']
    state = response['CityStateLookupResponse']['ZipCode']['State']
    city.strip()
    state.strip()
    print('\nZip Code '+zip+' is located in '+city+', '+state)
    return city + ', ' + state


# Function takes the city and state returned by validateZip() and queries returns
# the county using the Google Maps API 
def getCounty(zip):
    payload = ''.join(["https://maps.googleapis.com/maps/api/geocode/xml?address=",
                       user_input,
                       "**** ENTER YOUR GOOGLE API KEY ****"])
    r = requests.get(payload)
    response = xm.parse(r.text)
    county = response['GeocodeResponse']['result']['address_component'][2]['long_name']
    state_s = response['GeocodeResponse']['result']['address_component'][3]['short_name']
    state_l = response['GeocodeResponse']['result']['address_component'][3]['long_name']
    county = county.replace(' County', '')
    county = str(county + ', ' + state_s)
    return {'county' : county, 'state_s' : state_s, 'state_l' : state_l}


# Function takes county returned by getCounty() and returns
# the county and state codes used by the Census Bureau
def getStateCountyCodes(dictionary):
    codes = pd.read_csv('https://lehd.ces.census.gov/data/schema/latest/label_geography.csv')
    county = dictionary['county']
    state = dictionary['state_l']
    state_code = codes.geography[(codes.geo_level == 'S')&(codes.label == state)].iloc[0]
    county_code = codes.geography[(codes.geo_level == 'C')&(codes.label == county)].iloc[0]
    county_code = county_code[2:]
    return {'state_code':state_code, 'county_code':county_code}


# Function takes city and county codes returned by getStateCountyCodes() and returns
# health insurance coverage in the county corresponding to the original zip code 
# entered by the user using the Census Bureau API
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
    new_header = df.iloc[0] 
    df = df[1:] 
    df.columns = new_header 
    df.iloc[:,1:6] = df.iloc[:,1:6].apply(pd.to_numeric)
    df.columns = ['Income-to-Poverty Ratio Group','Insured', 'Uninsured','Year','State Code', 'County Code']
    df['Uninsured %'] = df['Uninsured']/(df['Insured']+df['Uninsured'])
    return df


# Generates a chart with total # of insured and uninsured
# grouped by Income-to-Poverty Ratio Group
def generateBarChart_total(df): 
    insured = df['Insured']
    uninsured = df['Uninsured']
    
    ind = np.arange(len(df['Income-to-Poverty Ratio Group']))
    bar_width = 0.45
    
    fig, ax = plt.subplots()
    fig.set_size_inches(11, 8.5)
    bar1 = ax.bar(ind, insured, bar_width, align = 'center', alpha = 0.4 , color ='g', label = 'Insured')
    bar2 = ax.bar(ind + bar_width, uninsured, bar_width, align = 'center', alpha = 0.4 , color = 'r', label = 'Uninsured')
    
    county = county_results['county']
    ax.set_ylabel('Population', fontweight="bold")
    ax.set_title('Population with Health Insurance in \n' + county[:-4] + ' County', fontsize=16, fontweight="bold")
    ax.legend()
  
    mx = int(max(df['Insured'])*1.2)
    values = np.arange(0, mx, math.ceil((mx /20)/ 200000) * 200000)
    plt.yticks(values, ['%s' % ("{:,}".format(val)) for val in values])
    ax.set_xticks(ind + bar_width / 2)
    ax.set_xticklabels(('Group\n1', 'Group\n2', 'Group\n3', 'Group\n4', 'Group\n5','Group\n6'))

    for rect in bar1 + bar2:
            height = rect.get_height()
            ax.text(rect.get_x() + rect.get_width()/2.0, height, '%s' % ("{:,}".format(height)), ha='center', va='bottom')  # ("{:,}".format(val)
    plt.show()


# Generates a chart with percentage uninsured grouped by Income-to-Poverty Ratio Group
def generateBarChart_percent(df): 
    insured_per = df['Uninsured %']
    
    ind = np.arange(len(df['Income-to-Poverty Ratio Group']))
    bar_width = 0.75
    
    fig, ax = plt.subplots()
    fig.set_size_inches(11, 8.5)
    bar1 = ax.bar(ind, insured_per, bar_width, align = 'center', alpha = 0.4 , color ='r', label = '% Unsured')
    
    county = county_results['county']
    ax.set_ylabel('% of Population', fontweight="bold")
    ax.set_title('% Population with Health Insurance in \n' + county[:-4] + ' County', fontsize=16, fontweight = "bold")
    ax.legend()
    
    mx = max(df['Uninsured %']) * 1.2    
    values = np.arange(0, mx, math.ceil((mx / 20) / 0.02) * 0.02)
    plt.yticks(values, ['%s' % round(val * 100, 2) for val in values])
    ax.set_xticks(ind)
    ax.set_xticklabels(('Group\n1', 'Group\n2', 'Group\n3', 'Group\n4', 'Group\n5','Group\n6'))
    
    for rect in bar1:
            height = rect.get_height()
            ax.text(rect.get_x() + rect.get_width()/2, height, '%s' % round(height*100,2), ha='center', va='bottom')
    
    plt.show()
    
    
user_input = getInput()
city_state = validateZip(user_input)
county_results = getCounty(user_input)
codes = getStateCountyCodes(county_results)
insurance_data = getCensusData(codes)
generateBarChart_total(insurance_data)
generateBarChart_percent(insurance_data)
