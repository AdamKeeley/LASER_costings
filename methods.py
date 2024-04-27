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
        json_data = json.loads(response.text)
        nextPage = json_data['NextPageLink']
        items = json_data['Items']
        df = pd.json_normalize(items)
    return df

def vmQueryString(vm):
    with open("resources.json", "r") as f:
        parsed_json=json.load(f)
    query_vm = (
        "(armRegionName eq 'Global' " +
        f"or armRegionName eq '{parsed_json['TRE']['armRegionName']}') " 
    )
    query_vm = query_vm + (
        f"and (armSkuName eq '{vm}' " +
        "and priceType eq 'Consumption' " +
        "and contains(meterName, 'Spot') " +
        "and contains(productName, 'Windows') "
    )
    query_vm = query_vm + (
        f"or (meterName eq '{parsed_json['TRE']['VirtualMachine']['Required']['Disk']['meterName']}')) " 
    )
    return query_vm

result =(getPrices(vmQueryString(vm='Standard_D16s_v4')))
print(result)