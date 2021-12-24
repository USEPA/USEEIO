# USEEIO Model Versioning Scheme

USEEIO model names follow a scheme.
These model names are intended to identify a model by version and a set of key characteristics. 
They are independent of the software or authors producing the model.
They are not full model descriptions.


## Naming pattern
Model names are composed of parts in a clear pattern.
The naming pattern is a set sequence of these parts with required separator characters.
```
{prefix}{root} v{major}.{minor}.{update}{form}{sectors}-{IOyear}-{subset}
```

## Name parts
The following table define the parts of a model name.

| Name part | Definition | Format | Default|  Example |
|---|---|---|---|---|
| prefix | Primary model region | Two-letter state name for state models| Blank, assumes national model| `GA`|
| root   | Main model name | String | USEEIO | `USEEIO`|
| major  | Major version number. Advances indicate a major methodological/data update | Integer | NA | `2` |
| minor  | Minor version number. Advances indicate a minor methodological/data update | Integer | NA | `0` |
| update | Update number. Advances indicates a minor fix or data update | Integer | NA | `1` |
| form   | Indicator for CommodityxCommodity or IndustryxIndustry form | 'i' for IxI form | Blank, assumes default CXC | `i` |
| sectors<sup>1</sup> | Base level of BEA ([see definitions](https://www.bea.gov/sites/default/files/methodologies/industry_primer.pdf#page=17)) or number of sectors | <ul><li>Character for a BEA level - 's' for Summary, 'c' for Sector, OR</li><li>Integer for an arbitrary number<sup>2</sup></li></ul> | Blank, assumes Detail level | `s` or `75` |
| IOyear | Optional year of base input-output data | Integer | For deviation from IO year in base version | `2017` |
| subset | Short name for a satellite or indicator subset | Hyphen followed by 3-6 digit string with letter in CAPS | Blank, assumes all satellite tables available for that region are present | `-GHG` |

<sup>1</sup> If `sectors` is a letter, it means the model uses the original BEA Summary sectors; if it is a number, it means model sectors are hybridized (e.g. disaggregated and/or aggregated) and are not identical with the original BEA Summary sectors.

<sup>2</sup> If the previous part is also an integer, a hyphen will be added before the integer, e.g. `USEEIOv2.0-411`.

## Examples of model names

| Model Name | Interpretation |
|---|---|
| USEEIO v1.3-WASTE       | A national v1.3 model with only the waste satellite tables |
| USEEIO v2.0i75-2016-WAT | A national v2.0 model in industry form with 75 industries using 2016 IO tables and the water (WAT) satellite table and indicators |
| GAUSEEIOv2.0            | A GA model (in 2 region form) of the full v2.0 model |
| USEEIOv2.0is-GHG+       | A national v2.0 model in industry form at the BEA summary level with GHG table and customized GHG indicators (like 20 yr GWP) |

### Rules

1. Models with the same version number (major.minor.update) will use the same data sources, data years (except when IOyear is specified as something else) and currency year.
   
2. Model names do not indicate intended application or release status of models.

### Model IDs
Technically, any model version will also have a model ID.
Model IDs will capture information on the complete built models based on a hashing algorithm.









