import json
import requests
import pandas as pd
import numpy as np

def combinePrices():
    df = pd.DataFrame()
    with open("resources.json", "r") as f:
        parsed_json=json.load(f)
    for item in parsed_json['TRE']:
        result = getPrices(getQueryString(item))
        if isinstance(result, pd.DataFrame):
            result.insert(0, "resourceType", item, True)
            df = pd.concat([df, result], ignore_index=True)
        else: 
            print(f"Error fetching costs for TRE resourceType '{item}': {result}")
    return df

def getPrices(queryString):
    if queryString:
        api_url = f"https://prices.azure.com/api/retail/prices?currencyCode='GBP'&api-version=2021-10-01-preview"
        response = requests.get(api_url, params={'$filter': queryString})
        if response.status_code == 200:
            json_data = json.loads(response.text)
            nextPage = json_data['NextPageLink']
            items = json_data['Items']
            df = pd.json_normalize(items)
            while(nextPage):
                response = requests.get(nextPage)
                json_data = json.loads(response.text)
                nextPage = json_data['NextPageLink']
                items = json_data['Items']
                df = pd.concat([df, pd.json_normalize(items)], ignore_index=True)
            return df[df['tierMinimumUnits']==0]
        else:
            return f"Failure to fetch prices (status_code = {response.status_code})."
    else: 
        return "No queryString provided."

def getQueryStringElement(resourceType, elementType):
    with open("resources.json", "r") as f:
        parsed_json=json.load(f)
    
    query_element = ""
    query_element_list = []
    elements = parsed_json['TRE'][resourceType][elementType]
    if elements:
        for item in elements:
            if elements[item]['operator'] == 'eq':
                query_element_list.append (
                    f"{elements[item]['identifier']} " + 
                    f"{elements[item]['operator']} " + 
                    f"'{elements[item]['value']}'"
                )
            if elements[item]['operator'] == 'contains':
                query_element_list.append (
                    f"{elements[item]['operator']}" + 
                    f"({elements[item]['identifier']}, " + 
                    f"'{elements[item]['value']}')"
                )
        if elementType == 'Common':
            query_element = ' and '.join(query_element_list)
        if elementType == 'Component' or elementType == 'Required':
            query_element = ' or '.join(query_element_list)
    
    return query_element

def getQueryString(resourceType):
    with open("resources.json", "r") as f:
        parsed_json=json.load(f)
    
    query_region = (
        "(armRegionName eq 'Global' " +
        f"or armRegionName eq '{parsed_json['armRegionName']}') " 
        )
    query_common = getQueryStringElement(resourceType, 'Common')
    query_component = getQueryStringElement(resourceType, 'Component')
    query_required = getQueryStringElement(resourceType, 'Required')
    
    if query_common and query_component and query_required:
        query_full = f"{query_region} and ((({query_common}) and ({query_component})) or {query_required})"
    elif query_common and query_component:
        query_full = f"{query_region} and (({query_common}) and ({query_component}))"
    elif query_component and query_required:
        query_full = f"{query_region} and (({query_component}) or ({query_required}))"
    elif query_component:
        query_full = f"{query_region} and ({query_component})"
    else:
        query_full = ""
    return query_full

def calcCosts(df, storageVolume, vmHours):
    df = df[['resourceType', 'retailPrice', 'meterName', 'productName', 'skuName', 'serviceName', 'unitOfMeasure']]
    
    monthlyMultiplier = [
        [(df['unitOfMeasure'] == '1 GB/Month')                                              , df.retailPrice * storageVolume]
        , [(df['unitOfMeasure'] == '1 Hour') & (df['resourceType'] == 'VirtualMachine')     , df.retailPrice * vmHours]
        , [(df['unitOfMeasure'] == '1 Hour') & (df['resourceType'] == 'StorageAccount')     , df.retailPrice * 730]
        , [(df['unitOfMeasure'] == '1/Month')                                               , df.retailPrice * 1]
        , [(df['unitOfMeasure'] == '10K')                                                   , df.retailPrice * 10]
        ]

    df['monthlyCost'] = np.select([item[0] for item in monthlyMultiplier], [item[1] for item in monthlyMultiplier])
    df['annualCost'] = df['monthlyCost'] * 12

    return df
