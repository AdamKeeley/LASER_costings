import json
import requests
import pandas as pd

def combinePrices():
    df = pd.DataFrame()
    with open("resources.json", "r") as f:
        parsed_json=json.load(f)
    for item in parsed_json['TRE']:
        result = getPrices(getQueryString(item))
        if isinstance(result, pd.DataFrame):
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
    if parsed_json['TRE'][resourceType][elementType]:
        for item in parsed_json['TRE'][resourceType][elementType]:
            if parsed_json['TRE'][resourceType][elementType][item]['operator'] == 'eq':
                query_element_list.append (
                    f"{parsed_json['TRE'][resourceType][elementType][item]['identifier']} " + 
                    f"{parsed_json['TRE'][resourceType][elementType][item]['operator']} " + 
                    f"'{parsed_json['TRE'][resourceType][elementType][item]['value']}'"
                )
            if parsed_json['TRE'][resourceType][elementType][item]['operator'] == 'contains':
                query_element_list.append (
                    f"{parsed_json['TRE'][resourceType][elementType][item]['operator']}" + 
                    f"({parsed_json['TRE'][resourceType][elementType][item]['identifier']}, " + 
                    f"'{parsed_json['TRE'][resourceType][elementType][item]['value']}')"
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
