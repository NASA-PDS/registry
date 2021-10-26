package gov.nasa.pds.registry.mgr.dao;

import java.io.File;

import org.elasticsearch.client.Request;
import org.elasticsearch.client.Response;
import org.elasticsearch.client.ResponseException;
import org.elasticsearch.client.RestClient;

import gov.nasa.pds.registry.common.es.client.EsClientFactory;
import gov.nasa.pds.registry.common.es.client.EsUtils;
import gov.nasa.pds.registry.common.es.client.SearchResponseParser;
import gov.nasa.pds.registry.mgr.util.CloseUtils;
import gov.nasa.pds.registry.mgr.util.Logger;
import gov.nasa.pds.registry.mgr.util.es.EsDocWriter;


/**
 * Base abstract class to export data from Elasticsearch. Data is processed in batches. 
 * Elasticsearch "search_after" parameter is used to paginate search results.
 * 
 * @author karpenko
 *
 */
public abstract class DataExporter
{
    private static final int BATCH_SIZE = 100;
    private static final int PRINT_STATUS_SIZE = 5000;
    
    private String esUrl;
    private String indexName;
    private String authConfigFile;
    
   
    /**
     * Constructor
     * @param esUrl Elasticsearch URL, e.g., "http://localhost:9200"
     * @param indexName Elasticsearch index name
     * @param authConfigFile Elasticsearch authentication configuration file 
     * (see Registry Manager documentation for more info) 
     */
    public DataExporter(String esUrl, String indexName, String authConfigFile)
    {
        this.esUrl = esUrl;
        this.indexName = indexName;
        this.authConfigFile = authConfigFile;
    }
    
    
    /**
     * Create JSON query to pass to "/indexName/_search" Elasticsearch API.
     * @param batchSize batch size
     * @param searchAfter Elasticsearch "search_after" parameter to paginate search results.
     * @return JSON 
     * @throws Exception an exception
     */
    protected abstract String createRequest(int batchSize, String searchAfter) throws Exception;
    
    
    /**
     * Export data from Elasticsearch into a file
     * @param file a file
     * @throws Exception an exception
     */
    public void export(File file) throws Exception
    {
        EsDocWriter writer = null; 
        RestClient client = null;
        
        try
        {
            writer = new EsDocWriter(file);
            client = EsClientFactory.createRestClient(esUrl, authConfigFile);
            SearchResponseParser parser = new SearchResponseParser();
            
            String searchAfter = null;
            int numDocs = 0;
            
            do
            {
                Request req = new Request("GET", "/" + indexName + "/_search");
                // Call abstract method to get JSON query
                String json = createRequest(BATCH_SIZE, searchAfter);
                req.setJsonEntity(json);
                
                Response resp = client.performRequest(req);
                parser.parseResponse(resp, writer);
                
                numDocs += parser.getNumDocs();
                searchAfter = parser.getLastId();
                
                if(numDocs % PRINT_STATUS_SIZE == 0)
                {
                    Logger.info("Exported " + numDocs + " document(s)");
                }
            }
            while(parser.getNumDocs() == BATCH_SIZE);

            if(numDocs == 0)
            {
                Logger.info("No documents found");
            }
            else
            {
                Logger.info("Exported " + numDocs + " document(s)");
            }
            
            Logger.info("Done");
        }
        catch(ResponseException ex)
        {
            throw new Exception(EsUtils.extractErrorMessage(ex));
        }
        finally
        {
            CloseUtils.close(client);
            CloseUtils.close(writer);
        }

    }
}
