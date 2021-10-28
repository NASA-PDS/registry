package gov.nasa.pds.registry.common.es.client;


import java.security.SecureRandom;

import javax.net.ssl.SSLContext;
import javax.net.ssl.TrustManager;


/**
 * TLS/SSL utility methods.
 * 
 * @author karpenko
 */
public class SSLUtils
{
    /**
     * Create "trust all" SSL context to support self-signed certificates.
     * @return SSL context object
     * @throws Exception an exception
     */
    public static SSLContext createTrustAllContext() throws Exception
    {
        TrustManager[] trustManagers = new TrustManager[1];
        trustManagers[0] = new TrustAllManager();
        
        SSLContext sc = SSLContext.getInstance("SSL");
        sc.init(null, trustManagers, new SecureRandom());
        return sc;
    }
}
