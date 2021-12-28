# USEEIO Model Versioning Scheme

USEEIO model names follow a scheme.
These model names are intended to identify a model by version and a set of key characteristics. 
They are independent of the software (with the exception of the `build` identifier) or authors producing the model.
They are not full model descriptions.
A named model does not imply that the model has been reviewed or released. 

## Naming pattern
Model names are composed of parts in a clear pattern.
The naming pattern is a set sequence of these parts with separator characters that are required when the given part is present.
```
{loc}{root} v{major}.{minor}.{patch}+{build}-{form}{#sectors}-{#regions}r-{IOyear}-{subset}

```
The version number is the major.minor.patch sequence. The version number plus the build identifier follows [Semantic Versioning 2.0.0](http://semver.org/) for software with some adaptations appropriate for use for a computational model versioning scheme.

## Name parts
The following table define the parts of a model name.

| Name part | Definition | Format | Example | Assumed Value if Absent|
|---|---|---|---|---|
| loc   | Two-letter acronym for primary model location/region | string | `US`| not applicable|
| root  | Main model type | string | `EEIO`| not applicable|
| major | Major version number. Advances are for use of a new base IO schema | integer | `2` | not applicable|
| minor | Minor version number. Advances indicate a minor methodological/data update | integer |  `0` | not applicable|
| patch |  OPTIONAL. A patch number. Advances indicates a minor fix, format, or data update | integer | `1` | `0`|
| build |  OPTIONAL. A build identifier derived from software during model build time | string | `c2nde3d` | blank means not available|
| form  | OPTIONAL. Indicator for Commodity x Commodity or Industry x Industry form | 'c' for commodityxcommodity , 'i' for industryxindustry | `i` | `c`|
| #sectors<sup>1</sup> | OPTIONAL. Base level of BEA, ([see definitions](https://www.bea.gov/sites/default/files/methodologies/industry_primer.pdf#page=17)); or number of sectors | <ul><li>string for a BEA level - 'd' for detail, 's' for Summary, 'c' for Sector, OR</li><li>integer for an arbitrary number<sup>2</sup></li></ul> | `s` or `75` | `d` |
| #regions | OPTIONAL. Number of model regions when greater than 1 | integer | `2` | `1` |
| IOyear | OPTIONAL. Year of base input-output data. Used for deviations from the benchmark IO year of the major version | integer |  `2017` | IO data year for IO schema and major model version, see [Base IO Schema and Benchmark IO Data Year for Major Model Versions](#base-io-schema-and-benchmark-io-data-year-for-major-model-versions) |
| subset | OPTIONAL. Short name for a satellite or indicator subset or blank if full set is included | string, 3-6 digit, all CAPS |  `GHG` | All resource, emission and waste flow classes found in the most recent version with a complete set of tables|

<sup>1</sup> If `sectors` is a letter, it means the model uses the original BEA sectors associated with the given level; if it is a number, it means model sectors are disaggregated and/or aggregated.

## Base IO Schema and Benchmark IO Data Year for Major Model Versions

The base IO schema is the set of sector codes and names for commodities and industries.
USEEIO models have used the BEA IO schema, which is updated every 5 years along with the release of the benchmark, detailed level IO tables for the same year.
USEEIO models alter names for commodities in the schema and may add or remove sectors, and hence the IO schema is used as the base schema for the model but will not necessarily be identical to the model IO schema.

| Major Version | IO Schema | Benchmark IO Data Year |
|---|---|---|
| 1  | BEA 2007 | 2007 |
| 2  | BEA 2012 | 2012 |

## Examples of model names

| Model Name | Interpretation |
|---|---|
| USEEIO v1.3.0-WASTE       | A US v1.3.0 detailed level commodity form 1-region model using a 2007 base IO year with only the waste satellite tables |
| USEEIO v2.0.0-i75-2016-WAT | A US v2.0.0 75-industry form model using 2016 base IO data and the 2012 IO schema with only the water satellite table |
| GAEEIO v2.1.0-cs-2r        | A Georgia v2.1.0 BEA summary-level commodity model in 2 region form using a 2012 base IO year with all satellite tables and flows|
| USEEIO v2.0.0-is-GHG+    | A national v2.0.0 model in industry form at the BEA summary level with GHG table and customized GHG indicators (like 20 yr GWP) |

## Rules

1. Models with the same version number (major.minor.patch) will use the same data sources, data years (except when IOyear is specified as something else) and currency year.
   
