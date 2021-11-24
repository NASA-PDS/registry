package gov.nasa.pds.registry.common.es.client;


import java.security.cert.CertificateException;
import java.security.cert.X509Certificate;
import javax.net.ssl.X509TrustManager;


/**
 * This class is used for HTTPS connection configuration
 * to support self-signed certificates.
 * 
 * @author karpenko
 */
public class TrustAllManager implements X509TrustManager
{
    private X509Certificate[] certs;
    
    
    public TrustAllManager()
    {
        certs = new X509Certificate[0];
    }
    
    
    @Override
    public void checkClientTrusted(X509Certificate[] chain, String authType) throws CertificateException
    {
    }

    
    @Override
    public void checkServerTrusted(X509Certificate[] chain, String authType) throws CertificateException
    {
    }

    
    @Override
    public X509Certificate[] getAcceptedIssuers()
    {
        return certs;
    }

}
