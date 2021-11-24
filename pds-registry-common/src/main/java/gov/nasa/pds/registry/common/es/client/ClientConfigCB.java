package gov.nasa.pds.registry.common.es.client;

import javax.net.ssl.SSLContext;

import org.apache.http.auth.AuthScope;
import org.apache.http.auth.UsernamePasswordCredentials;
import org.apache.http.client.CredentialsProvider;
import org.apache.http.conn.ssl.TrustSelfSignedStrategy;
import org.apache.http.impl.client.BasicCredentialsProvider;
import org.apache.http.impl.nio.client.HttpAsyncClientBuilder;
import org.apache.http.ssl.SSLContextBuilder;
import org.apache.http.ssl.SSLContexts;
import org.elasticsearch.client.RestClientBuilder;


/**
 * Implementation of Elasticsearch client API's HTTP configuration callback.
 * This class is used to setup TLS/SSL and authentication.
 * 
 * @author karpenko
 */
public class ClientConfigCB implements RestClientBuilder.HttpClientConfigCallback
{
    private boolean trustSelfSignedCert = false;
    private CredentialsProvider credProvider;

    
    /**
     * Constructor
     */
    public ClientConfigCB()
    {
    }

    
    /**
     * Set to true to trust self-signed certificates.
     * @param b Set to true to trust self-signed certificates.
     */
    public void setTrustSelfSignedCert(boolean b)
    {
        this.trustSelfSignedCert = b;
    }

    
    /**
     * Set user name and password for basic authentication.
     * @param user user name
     * @param pass password
     */
    public void setUserPass(String user, String pass)
    {
        if(user == null || pass == null) return;
        
        credProvider = new BasicCredentialsProvider();
        credProvider.setCredentials(AuthScope.ANY, new UsernamePasswordCredentials(user, pass));
    }
    
    
    @Override
    public HttpAsyncClientBuilder customizeHttpClient(HttpAsyncClientBuilder httpClientBuilder)
    {
        try
        {
            if(trustSelfSignedCert)
            {
                confTrustSelfSigned(httpClientBuilder);
            }

            if(credProvider != null)
            {
                httpClientBuilder.setDefaultCredentialsProvider(credProvider);
            }
            
            return httpClientBuilder;
        }
        catch(Exception ex)
        {
            throw new RuntimeException(ex);
        }
    }

    
    private void confTrustSelfSigned(HttpAsyncClientBuilder httpClientBuilder) throws Exception
    {
        SSLContextBuilder sslBld = SSLContexts.custom(); 
        sslBld.loadTrustMaterial(new TrustSelfSignedStrategy());
        SSLContext sslContext = sslBld.build();

        httpClientBuilder.setSSLContext(sslContext);
    }
    
}
