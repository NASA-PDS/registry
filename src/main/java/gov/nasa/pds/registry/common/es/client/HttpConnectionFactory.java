package gov.nasa.pds.registry.common.es.client;


import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.Base64;

import javax.net.ssl.HttpsURLConnection;
import javax.net.ssl.SSLContext;

import org.apache.http.HttpHost;

import gov.nasa.pds.registry.common.util.JavaProps;


/**
 * Factory class to create HTTP connections.
 * 
 * @author karpenko
 */
public class HttpConnectionFactory
{
    private int timeout = 5000;
    private URL url;
    private HttpHost host;
    private String authHeader;

    
    /**
     * Constructor.
     * @param esUrl Elasticsearch URL, e.g., "http://localhost:9200"
     * @param indexName Elasticsearch index name.
     * @param api API name, e.g., "_bulk".
     * @throws Exception an exception
     */
    public HttpConnectionFactory(String esUrl, String indexName, String api) throws Exception
    {
        HttpHost host = EsUtils.parseEsUrl(esUrl);
        this.url = new URL(host.toURI() + "/" + indexName + "/" + api);
    }
    
    
    /**
     * Create HTTP connection
     * @return HTTP connection
     * @throws Exception an exception
     */
    public HttpURLConnection createConnection() throws Exception
    {
        HttpURLConnection con = (HttpURLConnection)url.openConnection();
        con.setConnectTimeout(timeout);
        con.setReadTimeout(timeout);
        con.setAllowUserInteraction(false);
        
        if(authHeader != null)
        {
            con.setRequestProperty("Authorization", authHeader);
        }
        
        return con;
    }

    
    /**
     * Set connection timeout in seconds.
     * 
     * @param timeoutSec timeout in seconds
     */
    public void setTimeoutSec(int timeoutSec)
    {
        if(timeoutSec <= 0) throw new IllegalArgumentException("Timeout should be > 0");
        this.timeout = timeoutSec * 1000;
    }

    
    /**
     * Get host name
     * @return host name
     */
    public String getHostName()
    {
        return host.getHostName();
    }
    
    
    /**
     * Set user name and password for basic authentication
     * @param user user name
     * @param pass password
     */
    public void setBasicAuthentication(String user, String pass)
    {
        String auth = user + ":" + pass;
        String b64auth = Base64.getEncoder().encodeToString(auth.getBytes(StandardCharsets.UTF_8));
        this.authHeader = "Basic " + b64auth;
    }
    
    
    /**
     * Setup authentication parameters and TLS/SSL.  
     * @param authConfigFile Authentication configuration file.
     * @throws Exception an exception
     */
    public void initAuth(String authConfigFile) throws Exception
    {
        if(authConfigFile == null) return;
        
        JavaProps props = new JavaProps(authConfigFile);
        
        // Trust self-signed certificates
        if(Boolean.TRUE.equals(props.getBoolean(ClientConstants.AUTH_TRUST_SELF_SIGNED)))
        {
            SSLContext sslCtx = SSLUtils.createTrustAllContext();
            HttpsURLConnection.setDefaultSSLSocketFactory(sslCtx.getSocketFactory());
        }
        
        // Basic authentication
        String user = props.getProperty("user");
        String pass = props.getProperty("password");
        if(user != null && pass != null)
        {
            setBasicAuthentication(user, pass);
        }
    }

}
