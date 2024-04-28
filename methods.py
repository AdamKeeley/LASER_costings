import json
import requests
import pandas as pd

def getPrices(queryString):
    api_url = f"https://prices.azure.com/api/retail/prices?currencyCode='GBP'&api-version=2021-10-01-preview"
    response = requests.get(api_url, params={'$filter': queryString})
    print(response.status_code)
    json_data = json.loads(response.text)
    nextPage = json_data['NextPageLink']
    items = json_data['Items']
    df = pd.json_normalize(items)
    while(nextPage):
        response = requests.get(nextPage)
        print(response.status_code)
        json_data = json.loads(response.text)
        nextPage = json_data['NextPageLink']
        items = json_data['Items']
        df = pd.concat([df, pd.json_normalize(items)])
    return df[df['tierMinimumUnits']==0]

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
