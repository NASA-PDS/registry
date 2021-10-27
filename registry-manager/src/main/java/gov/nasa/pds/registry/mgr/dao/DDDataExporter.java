package gov.nasa.pds.registry.mgr.dao;

/**
 * Exports data dictionary records from Elasticsearch into a file.
 *  
 * @author karpenko
 */
public class DDDataExporter extends DataExporter
{
    /**
     * Constructor
     * @param esUrl Elasticsearch URL
     * @param indexName Elasticsearch index name
     * @param authConfigFile authentication configuration file
     */
    public DDDataExporter(String esUrl, String indexName, String authConfigFile)
    {
        super(esUrl, indexName + "-dd", authConfigFile);
    }

    
    /**
     * Creates Elasticsearch JSON query.
     */
    @Override
    protected String createRequest(int batchSize, String searchAfter) throws Exception
    {
        RegistryRequestBuilder reqBld = new RegistryRequestBuilder();
        String json = reqBld.createExportAllDataRequest("es_field_name", batchSize, searchAfter);
        return json;
    }

}
