package gov.nasa.pds.registry.mgr.dao;

import org.elasticsearch.client.Request;
import org.elasticsearch.client.Response;
import org.elasticsearch.client.RestClient;


/**
 * Data Access Object (DAO) to work with Elasticsearch indices.
 *  
 * @author karpenko
 */
public class IndexDao
{
    private RestClient client;
    
    /**
     * Constructor
     * @param client Elasticsearch client
     */
    public IndexDao(RestClient client)
    {
        this.client = client;
    }
    
    /**
     * Check if Elasticsearch index exists
     * @param indexName Elasticsearch index name
     * @return true if the index exists
     * @throws Exception an exception
     */
    public boolean indexExists(String indexName) throws Exception
    {
        Request req = new Request("HEAD", "/" + indexName);
        Response resp = client.performRequest(req);
        return resp.getStatusLine().getStatusCode() == 200;
    }

}
