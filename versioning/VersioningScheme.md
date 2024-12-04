# Model Naming Scheme

USEEIO model names follow a scheme. 
This document defines and describes the current naming scheme.
These model names are intended to identify a model by version and a set of key characteristics. 
They are independent of the software or authors producing the model.
They are not full model descriptions.
A named model does not imply that the model has been reviewed or released. 
Models named and created prior to the advent of this versioning scheme are not renamed. 

## Naming pattern
Model names are composed of parts in a clear pattern.
The naming pattern is a set sequence of these parts with separator characters that are required when the given part is present.
```
{loc}{root} v{major}.{minor}.{patch}-{alias}-{YY}
```
The version number is the major.minor.patch sequence. The version number plus the build identifier follows [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html) for software with some adaptations appropriate for use for a computational model versioning scheme.
Note that model specficiation files will not include spaces in the file name.

## Name parts
The following table defines the parts of a model name.

| Name part | Definition                                                                                                          | Format                      | Example    | Assumed Value if Absent                                                                                                                                                                           |
|-----------|---------------------------------------------------------------------------------------------------------------------|-----------------------------|------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| loc       | Two-letter acronym for primary model location/region. `US` for national models, and state acronym for state models. A collection of state models may use the loc prefix `State` | string                      | `US`       | not applicable                                                                                                                                                                                    |
| root      | Main model type                                                                                                     | string                      | `EEIO`     | not applicable                                                                                                                                                                                    |
| major     | Major version number indicating the generation of the model                                                         | integer                     | `2`        | not applicable                                                                                                                                                                                    |
| minor     | Minor version number indicating a minor methodological/data update                                                  | integer                     | `0`        | not applicable                                                                                                                                                                                    |
| patch     | OPTIONAL. A patch number indicating a minor fix, format, or data update                                             | integer                     | `1`        | `0`                                                                                                                                                                                               |
| alias     | See alias                                                                                                           | name                        | `redstart` | not applicable                                                                                                                                                                                    |
| YY        | Last two digits of year of key data.                                                                                | integer                     | `17`       | IO data year for IO schema and major model version, see [Base IO Schema and Benchmark IO Data Year for Major Model Versions](#base-io-schema) |

## Model Version
National and state models have separate versioning. 
The combination of the minor and major version reflect the model components that are included or their derivation.

## Alias
Each unique set of model data components and model attributes, not including the location or year, has an alias.
The alias names are drawn from name lists that capture some aspect of [americana](https://en.wikipedia.org/wiki/Americana_(culture)) or the natural environment of the U.S.
The aliases are chosen with a random script given a common set of names used for a generation and geo-resolution of models. 
For example v1 state models aliases are drawn from names of American pies; v2 national models aliases are drawn from names of U.S. songbirds that migrate in the winter.

## Base IO Schema 
The base IO schema is the set of sector codes and names for commodities and industries.
USEEIO models have used the BEA IO schema, which is updated every 5 years along with the release of the benchmark, detailed level IO tables for the same year.
USEEIO models alter names for commodities in the schema and may add or remove sectors, and hence the IO schema is used as the base schema for the model but will not necessarily be identical to the model IO schema.

| Major / Minor Version | Base IO Schema |
|-----------------------|----------------|
| 1.0                   | BEA 2007       |
| 2.0                   | BEA 2012       |
| 2.2 - 2.?             | BEA 2017       |

## Examples of model names

| Model Name              | Interpretation                                                                                                           |
|-------------------------|--------------------------------------------------------------------------------------------------------------------------|
| USEEIO v2.3-redstart-24 | A national version 2.3 model built using the 'redstart' collection of data and attributes and representing the year 2024 |
| MEEEIO v1.1-crawfish-22 | A Maine version 1.1 model built using the 'crawfish' collection of data and attributes and representing the year 2022   |

