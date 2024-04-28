import json
import requests
import pandas as pd

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
                df = pd.concat([df, pd.json_normalize(items)])
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
    
# TODO: align VM logic with that of Storage iteration
def vmQueryString(vm):
    with open("resources.json", "r") as f:
        parsed_json=json.load(f)
    query_region = (
        "(armRegionName eq 'Global' " +
        f"or armRegionName eq '{parsed_json['TRE']['armRegionName']}') " 
        )
    query_vm = (
        f"armSkuName eq '{vm}' " +
        "and priceType eq 'Consumption' " +
        "and contains(meterName, 'Spot') " +
        "and contains(productName, 'Windows') "
        )
    query_required = ""
    for item in parsed_json['TRE']['VirtualMachine']['Required']:
        if parsed_json['TRE']['VirtualMachine']['Required'][item]["identifier"] and parsed_json['TRE']['VirtualMachine']['Required'][item]["value"]:
            query_required = (
                f"({parsed_json['TRE']['VirtualMachine']['Required'][item]["identifier"]} " + 
                f"eq '{parsed_json['TRE']['VirtualMachine']['Required'][item]["value"]}') " 
                )

    if query_required:
        query_full = f"{query_region} and ({query_vm} or {query_required})"
    else:
        query_full = f"{query_region} and {query_vm}"

    return query_full

def storageQueryString():
    with open("resources.json", "r") as f:
        parsed_json=json.load(f)
    query_region = (
        "(armRegionName eq 'Global' " +
        f"or armRegionName eq '{parsed_json['TRE']['armRegionName']}') " 
        )
    
    query_storage_common = ""
    query_storage_common_list = []
    if parsed_json['TRE']['StorageAccount']['Common']:
        for item in parsed_json['TRE']['StorageAccount']['Common']:
            query_storage_common_list.append (
                f"{parsed_json['TRE']['StorageAccount']['Common'][item]['identifier']} " + 
                f"eq '{parsed_json['TRE']['StorageAccount']['Common'][item]['value']}'"
            )
        query_storage_common = ' and '.join(query_storage_common_list)
    
    query_storage_component = ""
    query_storage_component_list = []
    if parsed_json['TRE']['StorageAccount']['Component']:
        for item in parsed_json['TRE']['StorageAccount']['Component']:
            query_storage_component_list.append(
                f"{parsed_json['TRE']['StorageAccount']['Component'][item]['identifier']} " + 
                f"eq '{parsed_json['TRE']['StorageAccount']['Component'][item]['value']}'"
            )
        query_storage_component = ' or '.join(query_storage_component_list)

    query_required = ""
    query_required_list = []
    if parsed_json['TRE']['StorageAccount']['Required']:
        for item in parsed_json['TRE']['StorageAccount']['Required']:
            if parsed_json['TRE']['StorageAccount']['Required'][item]["identifier"] and parsed_json['TRE']['StorageAccount']['Required'][item]["value"]:
                query_required_list.append (
                    f"{parsed_json['TRE']['StorageAccount']['Required'][item]["identifier"]} " + 
                    f"eq '{parsed_json['TRE']['StorageAccount']['Required'][item]["value"]}'" 
                )
            query_required = ' or '.join(query_required_list)

    if query_required:
        query_full = f"{query_region} and ((({query_storage_common}) and ({query_storage_component})) or {query_required})"
    else:
        query_full = f"{query_region} and (({query_storage_common} and ({query_storage_component})"

    return query_full
