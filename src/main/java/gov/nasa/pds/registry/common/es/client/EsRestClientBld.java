package gov.nasa.pds.registry.common.es.client;

import org.apache.http.HttpHost;
import org.elasticsearch.client.RestClient;
import org.elasticsearch.client.RestClientBuilder;

import gov.nasa.pds.registry.common.util.JavaProps;


/**
 * Utility class to build Elasticsearch rest client.
 * 
 * @author karpenko
 */
public class EsRestClientBld
{
    private RestClientBuilder bld;
    private ClientConfigCB clientCB;
    private RequestConfigCB reqCB;
    
   
    /**
     * Constructor.
     * @param url Elasticsearch URL, e.g., "http://localhost:9200"
     * @throws Exception an exception
     */
    public EsRestClientBld(String url) throws Exception
    {
        HttpHost host = EsUtils.parseEsUrl(url);
        bld = RestClient.builder(host);
        
        clientCB = new ClientConfigCB();
        reqCB = new RequestConfigCB();
    }
    
    
    /**
     * Build the Elasticsearch rest client
     * @return Elasticsearch rest client
     */
    public RestClient build() 
    {
        bld.setHttpClientConfigCallback(clientCB);
        bld.setRequestConfigCallback(reqCB);
        
        return bld.build();
    }
    
    
    /**
     * Configure authentication
     * @param props properties
     * @throws Exception an exception
     */
    public void configureAuth(JavaProps props) throws Exception
    {
        if(props == null) return;

        // Trust self-signed certificates
        if(Boolean.TRUE.equals(props.getBoolean(ClientConstants.AUTH_TRUST_SELF_SIGNED)))
        {
            clientCB.setTrustSelfSignedCert(true);
        }
        
        // Basic authentication
        String user = props.getProperty("user");
        String pass = props.getProperty("password");
        if(user != null && pass != null)
        {
            clientCB.setUserPass(user, pass);
        }
    }
}
