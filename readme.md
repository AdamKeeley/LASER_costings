# Cost Estimates for defined Azure architecture
Effort to utilise [Azure Retail Prices REST API](https://learn.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices) to fetch cost estimates for TREs.  

Plan is to programmatically generate `$filter` strings that can be passed to getPrices method and fetch prices from API.  

Ultimately users will be able to choose VM size(s) and quantity along with storage volume and receive a monthly/annual cost estimate for a TRE of that specification.  

Costs of additional resources required for a functional TRE will be included, defined in a separate file (*.json?).  

Initially Type A TREs will be covered but should be extensible to include Type B & C eventually.  

```mermaid
flowchart TD
    A(Select spec) --> B(Generate `$filter` strings)
    B --> C(Make API calls)
    C --> D(Virtual Machines)
    C --> E(Storage Account)
    C --> F(Shared Resources)
    D --> G(Combine dataframes)
    E --> G
    F --> G
    G --> H(Calculate monthly/annual costs)
```

## getPrices(queryString)
Method to fetch the results from Azure Retail Prices REST API.  
Takes a string variable as a url `$filter` and returns a dataframe containing result of an API call.  
Currency code (GBP) embedded in api url.  

```python
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
```

## TRE Design
 
This should be applied to every `$filter` string query:
```
(armRegionName eq 'Global' or armRegionName eq 'uksouth')
```
Basic elements of a standard (Type A) TRE:  

### VMs
Each VM in a TRE requries the following:
|Resource|Identifed by|Example value|Additional parameters|
|---|---|---|---|
|Virtual Machine|`armSkuName`|'Standard_D16s_v4'|`and priceType eq 'Consumption'` <br> `and contains(meterName, 'Spot')` <br> `and contains(productName, 'Windows')`|
|Managed Disk|`metername`|'E10 LRS Disk'|
|Network Interface*|Unknown|Unknown|

*Appears there may be no non-negligable costs associated with Network Interface.  

### Storage Account
Each Storage Account (usually just the one) in a TRE requries the following:
|Resource|Identifed by|Example value|
|---|---|---|
|Storage Account|||
|Private Endpoint|`meterName`|'Standard Private Endpoint'|
|Network Interface*|unknown|unknown|

*Appears there may be no non-negligable costs associated with Network Interface.  

Potentially useful?
- meterNames
    - storageStored = 'Hot ZRS Data Stored'
    - storageWrite = 'Hot ZRS Write Operations'
    - storageList = 'Hot ZRS List Operations'
    - storageRead = 'Hot Read Operations'
    - storageOther = 'Hot Other Operations'
- productNames
    - storageProduct = 'Files v2'
- skuNames
    - storageSku = 'Hot ZRS'

### Shared Resources
Resources needed for and shared across each TRE:  
|Resource|Identifed by|Example value|
|---|---|---|
|Disk Encryption Set|||
|Recovery Services vault|||
|Network security group|||

