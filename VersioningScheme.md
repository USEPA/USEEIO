# USEEIO Model Versioning Scheme

USEEIO model names follow a scheme.
These model names are intended to identify a model by version and a set of key characteristics. 
They are independent of the software or authors producing the model.
They are not full model descriptions.


## Naming pattern
Model name are composed of parts in a clear 
The naming pattern is a set sequence of these parts with required separator characters.
```
{prefix}{root} v{major}.{minor}.{update}{form}{sectors}-{IOyear}-{subset}
```

## Name parts
The following table define the parts of a model name.

|Name part | Definition | Format | Default|  Example|
|---|---|---|---|---|
| prefix | Primary model region | Two-letter state name for state models| Blank, assumes national model| `GA`|
|root | Main model name |String| USEEIO | `USEEIO`|
|major |  Major version number. Advances indicate a major methodological/data update | Integer | NA | `2`|
|minor | Minor version number. Advances indicate a minor methodological/data update | Integer| NA| `0`|
|update| Update number. Advances indicates a minor fix or data update| Integer| NA| `1`|
|form| Indicates CommodityxCommodity or IndustryxIndustry | 'i' for IxI form | Blank, assumes default CXC| `i`|
|sectors | Base level of BEA ([see definitions](https://www.bea.gov/sites/default/files/methodologies/industry_primer.pdf#page=17) or number of sectors | Characters for a defined level - 's' for summary level, 'c' for sector level; Integers for an arbitrary number | Blank, assumes detailed level| `s` or `75`|
|IOyear|Optional year of base input-output data|Integer|For deviations from number of sectors in base version|`2017`|
|subset| A short name for a satellite or indicator subset | hyphen followed by 3-6 digit string with letter in CAPS | Blank, assumes all satellite tables available for that region are present| `-GHG`

## Examples of model names

|Model Name|Interpretation|
|---|---|
|USEEIO v1.3-WASTE|A national model v1.3 with only the waste satellite tables|
|USEEIO v2.0i75-2016-WAT| A national v2.0 model in industry form with 75 industries using 2016 IO tables and the water (WAT) satellite table and indicators
|GAUSEEIOv2.0|A GA model (in 2 region form) of the full v2.0 model|
|USEEIOv2.0is-GHG+|The 2.0 version in industry form at the BEA summary level with GHG table and customized GHG indicators (like 20 yr GWP)|

### Rules

1. Models with the same version number (major.minor.update) will use the same data sources, data years (except when IOyear is specified as something else) and currency year.
   
2. Model names do not indicate intended application or release status of models.
   
### Model IDs
Technically, any model version will also have a model ID. Model IDs will capture information on the complete built models based on a hashing algorithm.









