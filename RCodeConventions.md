# USEEIO Contributors R Coding Conventions

General practices for coding in R for use in R packages 

## Naming conventions

### Variable
Variable name should use UpperCamelCase (StateDirectDemand).

### Function
Function name should start with a verb in non-caps. Common operations should use common verbs..do not use synomyms without reason.

The following keywords and succeeding nouns should use title capitalization.

Prepositions should be in non-caps.

Avoid underscore in variable and function names.

Variable name should be non-caps.

    Nouns should be set up like state = "Georgia", state_acronym = "GA", location = "United States", location_acronym = "US" (with quotation marks)

    Numbers should be set up like referenceyear = 2013 (without quotation marks)

In addition, follow [these rules](http://codebuild.blogspot.com/2012/02/15-best-practices-of-variable-method.html).

## File and Data conventions

Large data files are not stored in github repositories and not included in R packages. 

Data are stored in the code repository under the conditions:
They are from static files that are not frequently updated or readily available and they may be used more than once.
They are not exceeding 1MB.

## Program structure conventions

We generally follow the [R packages book](https://r-pkgs.org/) conventions for creating R packages.

Functions should ideally do a perform a single abstract function well Reference: [tidy tools manifesto](https://cran.r-project.org/web/packages/tidyverse/vignettes/manifesto.html).

Avoid mixing side-effects with transformations. Ensure each function either returns an object, or has a side-effect. Don?t do both. Reference: [tidy tools manifesto](https://cran.r-project.org/web/packages/tidyverse/vignettes/manifesto.html).

When performing the same type of operation on data, use the same function from the same package, unless there is good reason not do.
