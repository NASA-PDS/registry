package gov.nasa.pds.registry.common.es.client;


import org.apache.http.client.config.RequestConfig;
import org.elasticsearch.client.RestClientBuilder;


/**
 * Implementation of Elasticsearch client API's request configuration callback.
 * This class is used to setup connection timeouts.
 * 
 * @author karpenko
 */
public class RequestConfigCB implements RestClientBuilder.RequestConfigCallback
{
    private int connectTimeoutSec = 5;
    private int socketTimeoutSec = 10;
    
    
    /**
     * Constructor
     */
    public RequestConfigCB()
    {
    }

    
    /**
     * Constructor
     * @param connectTimeoutSec connection timeout in seconds
     * @param socketTimeoutSec socket timeout in seconds
     */
    public RequestConfigCB(int connectTimeoutSec, int socketTimeoutSec)
    {
        this.connectTimeoutSec = connectTimeoutSec;
        this.socketTimeoutSec = socketTimeoutSec;
    }

    
    @Override
    public RequestConfig.Builder customizeRequestConfig(RequestConfig.Builder bld)
    {
        bld.setConnectTimeout(connectTimeoutSec * 1000);
        bld.setSocketTimeout(socketTimeoutSec * 1000);
        return bld;
    }

}
