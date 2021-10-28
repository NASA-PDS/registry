package gov.nasa.pds.registry.common.es.client;


import org.elasticsearch.client.RestClient;
import gov.nasa.pds.registry.common.util.JavaProps;


/**
 * A factory class to create Elasticsearch Rest client instances.
 * 
 * @author karpenko
 */
public class EsClientFactory
{
    /**
     * Create Elasticsearch rest client.
     * @param esUrl Elasticsearch URL, e.g., "http://localhost:9200"
     * @param authPath Path to authentication configuration file.
     * @return Elasticsearch rest client instance.
     * @throws Exception an exception
     */
    public static RestClient createRestClient(String esUrl, String authPath) throws Exception
    {
        EsRestClientBld bld = new EsRestClientBld(esUrl);
        
        if(authPath != null)
        {
            JavaProps props = new JavaProps(authPath);
            bld.configureAuth(props);
        }
        
        return bld.build();
    }

}
