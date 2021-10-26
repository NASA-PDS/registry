package gov.nasa.pds.registry.mgr.dao;

/**
 * Exports data records from Elasticsearch "registry" index into a file.
 * 
 * @author karpenko
 */
public class RegistryDataExporter extends DataExporter
{
    private String filterFieldName;
    private String filterFieldValue;

    
    /**
     * Constructor
     * @param esUrl Elasticsearch URL
     * @param indexName Elasticsearch index name
     * @param authConfigFile authentication configuration file
     */
    public RegistryDataExporter(String esUrl, String indexName, String authConfigFile)
    {
        super(esUrl, indexName, authConfigFile);
    }
    

    /**
     * Filter data by LIDVID, LID, PackageId, etc. 
     * If a filter is not set, all data will be exported.
     * @param name Elasticsearch field name
     * @param value field value
     */
    public void setFilterField(String name, String value)
    {
        this.filterFieldName = name;
        this.filterFieldValue = value;
    }
    
    
    /**
     * Create Elasticsearch JSON query.
     */
    @Override
    protected String createRequest(int batchSize, String searchAfter) throws Exception
    {
        RegistryRequestBuilder reqBld = new RegistryRequestBuilder();
        
        String json = (filterFieldName == null) ? 
                reqBld.createExportAllDataRequest("lidvid", batchSize, searchAfter) :
                reqBld.createExportDataRequest(filterFieldName, filterFieldValue, "lidvid", batchSize, searchAfter);

        return json;
    }

}
