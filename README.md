# renthse
rent house in hk


# Scripts
All scripts should be executed at / where you can see a package *renthse*

## Crawling house data from provider
In table *House*, there's  a column *source_type INTEGER* to identify which the row is from which source.

Source type
 * 1: [591.com](http://rent.591.com.hk/)
 * 2: [hk.centanet.com](http://hk.centanet.com/findproperty/zh-HK/Home/SearchResult/)
 * 3: [28hse.com](http://www.28hse.com)
 
# Requirement
1. Have python 2.7 installed (not tested on python 3) to run cralwing scripts
2. Have sqlite3 installed to examine db

# Setup
1. git clone git@github.com:warenix/renthse.git


### Fetching from Provider
Usage: _python provider.py -p <provider>_

Example: _python renthse/provider.py -p 591_

Output: all entries are inserted/ updated into a sqlite3 database, test.db

Available providers:
 * 591
 * centanet
 * hse28

## Reverse geocoding address
1. Get a free api key at [opencagedata](https://developer.opencagedata.com/)
2. Modify /renthse/extapi/OpenCage.py
3. Find and replace line \_\_key = None with \_\_key = '< MY KEY >'

Command: _python renthse/worker.py_

## Example use of the db

### Count total number of records crawled
Command: _sqlite3 test.db 'select count(*) from house;'_ 

Output: total number of records crawled

Sample Output:

```
4158
```

### Listing the top 10 expensive house 
Command: _sqlite3 test.db 'select * from house order by price desc limit 10'_

Output: top 10 expensive house

Sample Output:

```
430000|山頂/南區|The Mount Austin
400000|貝沙灣|貝沙灣
400000|山頂/南區|山頂道
398000|貝沙灣|貝沙灣 5期  洋房
380000|山頂/南區|甘道
350000|山頂/南區|Overbays
348000|貝沙灣|貝沙灣 5期  洋房
348000|貝沙灣|貝沙灣 5期  洋房
338000|貝沙灣|貝沙灣
330000|貝沙灣|貝沙灣 5期  洋房
```
