# VANDIX Calculator

A Docker container that calculates the Vancouver Area Neighborhood Deprivation Index for varying geographies.

To use, make a folder in the current directory called `data`. Then run the following command, of course substituting the `C:\Users\David\data` filepath for whever your `data` folder is.

```
docker run -it -v C:\Users\David\data:/data/ dswanlund/vandix
```


Note that if you want to calculate VANDIX for dissemination areas that intersect with a particular shapefile, ensure that you put that shapefile in the data folder beforehand.

![Instructions](vandix_instruction.gif)
