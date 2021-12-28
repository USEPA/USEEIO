# USEEIO Model Versioning Scheme

USEEIO model names follow a scheme.
These model names are intended to identify a model by version and a set of key characteristics. 
They are independent of the software or authors producing the model.
They are not full model descriptions.
A named model does not imply that the model has been reviewed or released. 

## Naming pattern
Model names are composed of parts in a clear pattern.
The naming pattern is a set sequence of these parts with required separator characters.
```
{loc}{root} v{major}.{minor}.{patch}+{build}-{form}{#sectors}-{#regions}r-{IOyear}-{subset}

```
The version number is the major.minor.patch sequence. The version number plus the build identifier follows [Semantic Versioning 2.0.0](http://semver.org/) for software with some adaptations appropriate for use for a computational model versioning scheme.

## Name parts
The following table define the parts of a model name.

| Name part | Definition | Format | Example |
|---|---|---|---|
| loc   | Two-letter acronym for primary model location/region | string | `US`|
| root  | Main model type | string | `EEIO`|
| major | Major version number. Advances are for use of a new base IO schema | integer | `2` |
| minor | Minor version number. Advances indicate a minor methodological/data update | integer |  `0` |
| patch |  OPTIONAL. A patch number. Advances indicates a minor fix, format, or data update | integer | `1` |
| build |  OPTIONAL. A build identifier derived from software during model build time | string | `c2nde3d` |
| form  | OPTIONAL. Indicator for Commodity x Commodity or Industry x Industry form | 'c' for commodityxcommodity , 'i' for industryxindustry | `i` |
| #sectors<sup>1</sup> | OPTIONAL. Base level of BEA ([see definitions](https://www.bea.gov/sites/default/files/methodologies/industry_primer.pdf#page=17)) or number of sectors | <ul><li>string for a BEA level - 'd' for detail, 's' for Summary, 'c' for Sector, OR</li><li>integer for an arbitrary number<sup>2</sup></li></ul> | `s` or `75` |
| #regions | OPTIONAL. Number of model regions when greater than 1 | integer | `2` |
| IOyear | OPTIONAL. Year of base input-output data for deviation from IO year in base version | integer |  `2017` |
| subset | OPTIONAL. Short name for a satellite or indicator subset or blank if full set is included | string, 3-6 digit, all CAPS |  `GHG` |

<sup>1</sup> If `sectors` is a letter, it means the model uses the original BEA sectors associated with the given level; if it is a number, it means model sectors are disaggregated and/or aggregated.

## Examples of model names

| Model Name | Interpretation |
|---|---|
| USEEIO v1.3.0-WASTE       | A national v1.3.0 model with only the waste satellite tables |
| USEEIO v2.0.0-i75-2016-WAT | A national v2.0.0 model in industry form with 75 industries using 2016 IO tables and the water (WAT) satellite table and indicators |
| GAEEIO v2.0.0-2r           | A Georgia model in 2 region form of the full v2.0.0 model |
| USEEIO v2.0.0-is-GHG+     | A national v2.0.0 model in industry form at the BEA summary level with GHG table and customized GHG indicators (like 20 yr GWP) |

### Rules

1. Models with the same version number (major.minor.patch) will use the same data sources, data years (except when IOyear is specified as something else) and currency year.
   

### Model IDs
Technically, any model version will also have a model ID.
Model IDs will capture information on the complete built models based on a hashing algorithm.









