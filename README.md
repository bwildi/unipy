# unityrawdataexport
unityrawdataexport is a Python 3 package for pulling raw data from the Unity Analytics REST API. See the [Unity documentation](https://docs.unity3d.com/Manual/UnityAnalyticsRawDataExport.html) for more information on how this works.

## Installation

## Quickstart guide
Firstly, create a UnityDataImporter object and include your Unity project id and your API key:

```python
from unityrawdataexport import UnityDataImporter

upid = "aa43ae0a-a7a7-4016-ae96-e253bb126aa8"
key = "166291ff148b2878375a8e54aebb1549"
udi = UnityDataImporter(upid, key)
```

To pull data from the API you need to first either create a new data export, or use a data export that has been created previously. For the latter case, you need to get the export_id. The list_data_exports method can be used to identify previously created data exports:

```python
# Get a json of the metadata of all data exports
exports = udi.list_data_exports()

# get the id of the most recent export
export_id = exports[0]['id']
```

You can then use the get_data_export method to get a json of the data from this export:

```python
data = udi.get_data_export(export_id)
```
