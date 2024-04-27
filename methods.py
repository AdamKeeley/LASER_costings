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
    return df

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
