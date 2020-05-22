## USEEIO Model Versioning Scheme

USEEIO model names follow a scheme.
These model names are only intended to be model identifiers and not full model descriptions.
Each model version will have its own model description page.

The following table shows the parts of a model name.

|Name part | Definition | Format | Default| Part Example|
|---|---|---|---|---|
|Region prefix | Primary model region | Two-letter state name for state models| Blank, assumes national model| `GA`|
|Root name | Main model name |String| USEEIO | `USEEIO`|
|Major version number | Indicates a major methodological/data update | Integer | NA | `1`|
|Minor version number | Indicates a minor methodological/data update | Integer after a dot| NA| `.1`|
|Commodity or industry form| Indicates CommodityxCommodity or IndustryxIndustry | 'i' for IxI form | Blank, assumes default CXC| `i`|
|Level of Detail | Base level of BEA ([see definitions](https://www.bea.gov/sites/default/files/methodologies/industry_primer.pdf#page=17)) | 's' for summary level, 'c' for sector level | Blank, assumes detailed level| `s`|
|Satellite table/indicator subset | Names of subset of satellite tables used | hyphen followed by 3-6 digit string with letter in CAPS | Blank, assumes all satellite tables availble for that region are present| `-GHG`

### Full Examples

|Model Name|Interpretation|
|---|---|
|USEEIOv1.3-WASTE|A national model v1.3 with only the waste satellite tables|
|GAUSEEIOv2.0|A GA model (in 2 region form) of the full v2.0 model|
|USEEIOv2.0is-GHG+|The 2.0 version in industry form at the BEA summary level with GHG table and customzied GHG indicators (like 20 yr GWP)|

### Rules

1. Models with the same version number (major.minor) will use the same data sources, data years and currency year.
2. Model names do not indicate intended application or release status of models.
3. Future models may be hybridized or dissaggregated. This information will be captured in the version number.

### Build numbers
Technically, any model version will also have a build number. Build numbers will capture information on dates/systems/persons performing a model build and will be reported separately.







