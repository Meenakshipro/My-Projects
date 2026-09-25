# Traffic Violations - EDA Report

## Data Understanding
```
{'Rows': 2067761, 'Columns': 53, 'Duplicate rows': 34, 'Columns with missing values': 22, 'Total missing cells': 2790606}
```

## Most Common Violations
```
Description
DRIVER FAILURE TO OBEY PROPERLY PLACED TRAFFIC CONTROL DEVICE INSTRUCTIONS                   171274
FAILURE TO DISPLAY REGISTRATION CARD UPON DEMAND BY POLICE OFFICER                            91000
DRIVING VEHICLE ON HIGHWAY WITH SUSPENDED REGISTRATION                                        60761
DISPLAYING EXPIRED REGISTRATION PLATE ISSUED BY ANY STATE                                     58493
FAILURE OF INDIVIDUAL DRIVING ON HIGHWAY TO DISPLAY LICENSE TO UNIFORMED POLICE ON DEMAND     55565
DRIVER USING HANDS TO USE HANDHELD TELEPHONE WHILEMOTOR VEHICLE IS IN MOTION                  49504
DRIVER FAILURE TO STOP AT STOP SIGN LINE                                                      45003
EXCEEDING THE POSTED SPEED LIMIT OF 40 MPH                                                    44621
EXCEEDING THE POSTED SPEED LIMIT OF 35 MPH                                                    41581
DRIVING VEHICLE ON HIGHWAY WITHOUT CURRENT REGISTRATION PLATES AND VALIDATION TABS            38009
Name: count, dtype: int64
```

## Top Hotspots
```
Location
GEORGIA AVE @ COLESVILLE RD             4968
MONTGOMERY VILLAGE AVE @ RUSSELL AVE    4600
WAYNE AVE @ DALE DR                     4508
CONNECTICUT AVE @ DEAN RD               4278
GEORGIA AVE @ CONNECTICUT AVE           4114
GEORGIA AVE @ HEWITT AVE                4062
WOODFIELD RD @ EMORY GROVE RD           3691
COLESVILLE RD @ GEORGIA AVE             3674
GEORGIA AVE @ RANDOLPH RD               3418
RIVER RD @ ROYAL DOMINION DR            3176
Name: count, dtype: int64
```

## Violations by Time of Day
```
Time Of Day
Morning       526014
Afternoon     424703
Night         418521
Late Night    361238
Evening       337285
Name: count, dtype: int64
```

## Violations by Weekday
```
Day Of Week
Monday       281155
Tuesday      365332
Wednesday    339495
Thursday     324258
Friday       320861
Saturday     230883
Sunday       205777
Name: count, dtype: int64
```

## Violations by Month
```
Month
January      166400
February     175876
March        194062
April        178025
May          181654
June         160607
July         166841
August       167350
September    170084
October      172689
November     173576
December     160597
Name: count, dtype: int64
```

## Top Vehicle Makes
```
Make
TOYOTA           367418
HONDA            308429
FORD             187835
NISSAN           155980
CHEVROLET        151005
HYUNDAI           77502
DODGE             66195
ACURA             62875
BMW               59293
MERCEDES-BENZ     55619
Name: count, dtype: int64
```

## Top Vehicle Types
```
VehicleType
02 - AUTOMOBILE              1833630
05 - LIGHT DUTY TRUCK         108173
28 - OTHER                     35055
03 - STATION WAGON             28614
01 - MOTORCYCLE                19052
06 - HEAVY DUTY TRUCK          16426
29 - UNKNOWN                   11153
08 - RECREATIONAL VEHICLE       5502
19 - MOPED                      2308
25 - UTILITY TRAILER            1965
Name: count, dtype: int64
```

## Violations by Category
```
Violation Category
OTHER                     570885
SPEEDING                  360696
TRAFFIC CONTROL DEVICE    325908
REGISTRATION              323178
LICENSE                   212201
ALCOHOL/DUI                74666
LANE CHANGE                57026
CELL PHONE                 50285
CARELESS/NEGLIGENT         44743
SEAT BELT                  34809
INSURANCE                  13354
Name: count, dtype: int64
```

## Numeric Quick Stats
```
{'Year': {'mean': np.float64(2008.13), 'median': np.float64(2008.0), 'mode': np.float64(2007.0), 'skewness': np.float64(-0.209)}, 'Accident Severity Score': {'mean': np.float64(0.06), 'median': np.float64(0.0), 'mode': np.int64(0), 'skewness': np.float64(5.222)}}
```

## Numeric Variable Summary
```
               Year  Accident Severity Score
count  2.054064e+06             2.067761e+06
mean   2.008131e+03             6.156176e-02
std    6.890187e+00             2.985538e-01
min    1.961000e+03             0.000000e+00
25%    2.003000e+03             0.000000e+00
50%    2.008000e+03             0.000000e+00
75%    2.013000e+03             0.000000e+00
max    2.025000e+03             2.000000e+00
```

## Outlier Counts (IQR)
```
{'Year': 5236, 'Accident Severity Score': 94870}
```

## Violation Type Breakdown (%)
```
Violation Type
WARNING     52.70
CITATION    42.81
ESERO        4.44
SERO         0.04
Name: proportion, dtype: float64
```

## Correlation Between Numeric Variables
```
                            Year  Accident Severity Score
Year                     1.00000                 -0.00128
Accident Severity Score -0.00128                  1.00000
```

## Average Severity by Gender
```
Gender
F          0.06
M          0.06
UNKNOWN    0.03
Name: Accident Severity Score, dtype: float64
```

## Demographics vs Violation Type
```
Violation Type   CITATION  ESERO  SERO  WARNING
Race                                           
ASIAN               40918   5476    34    70224
BLACK              287221  27810   255   340139
HISPANIC           232536  26030   273   205082
NATIVE AMERICAN      1409    232     0     1875
OTHER               47509   5847    43    84430
WHITE              275687  26383   291   388057
```

## Accident Involvement
```
{'Total Violations': 2067761, 'Accident': '56,478 (2.73%)', 'Personal Injury': '25,109 (1.21%)', 'Property Damage': '45,141 (2.18%)', 'Fatal': '567 (0.03%)'}
```

## Insights
- 'DRIVER FAILURE TO OBEY PROPERLY PLACED TRAFFIC CONTROL DEVICE INSTRUCTIONS' is the most common violation (~8.3% of all stops).
- 'GEORGIA AVE @ COLESVILLE RD' is the busiest recorded location.
- Violations peak in March.

## Conclusion
- 2,067,761 clean rows with 2,790,606 missing cells remaining (mostly optional fields).
- Violation type, location, and time of day are the strongest patterns found.
- Data is structured and ready for the dashboard and further reporting.