Index of missing functionalities / things that need to be fixed



### data_manager.py

function:
```
    def manage_requests(db, process, domain, request_list, plugin, temp_folder, geo_db):
```
line 50:
```
    # Clean malformed URL info groups
    # TODO: Check the reason for the malformed ones
```
line 206:
```
    # TODO: Fix the popularity update DB procedure
    #db.call("ComputeResourcePopularityLevel", values=[resource.values["id"]])
```



### fingerprinter.py

function:
```
    def beautify_code(process, code, headers):
```
line 53:
```
    # TODO: Fix beautify_code bug (freezes with some js code e.g. pinterest.com)
```



### ORM.py

function:
```
    def main(process):
```
line 103:
```
    # TODO: Try to remove websites when unable to get info??
    #  -> if a connection problem happens all the websites will be removed...
```



### tracking_manager.py

function:
```
    def get_mouse_fingerprinting(url):
```
line 647:
```
    # TODO: Replace above bad functioning code with new alternative
    # Otherwise extract file and compute
```
