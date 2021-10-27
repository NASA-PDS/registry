package gov.nasa.pds.registry.mgr.util.file;

import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;

import javax.net.ssl.HostnameVerifier;
import javax.net.ssl.HttpsURLConnection;
import javax.net.ssl.SSLContext;
import javax.net.ssl.SSLSession;

import gov.nasa.pds.registry.common.es.client.SSLUtils;
import gov.nasa.pds.registry.mgr.util.CloseUtils;
import gov.nasa.pds.registry.mgr.util.Logger;

/**
 * File downloader with retry logic. 
 * By default, SSL certificate and host verification is disabled for HTTPS 
 * connections to support self-signed certificates. This can be turned off.
 *  
 * @author karpenko
 */
public class FileDownloader
{
    private int timeout = 5000;
    private int numRetries = 3;
    private boolean sslTrustAll = true;
    
    /**
     * Constructor
     */
    public FileDownloader()
    {
    }

    
    /**
     * Enable or disable SSL certificate and host validation to support 
     * self-signed certificates. By default, validation is disabled.
     * @param val boolean flag.
     */
    public void setSslTrustAll(boolean val)
    {
        this.sslTrustAll = val;
    }
   
    
    /**
     * Download a file from a URL. Retry several times on error.
     * @param fromUrl Download a file from this URL.
     * @param toFile Save to this file
     * @throws Exception an exception
     */
    public void download(String fromUrl, File toFile) throws Exception
    {
        int count = 0;
        
        while(true)
        {
            try
            {
                count++;
                downloadOnce(fromUrl, toFile);
                return;
            }
            catch(Exception ex)
            {
                Logger.error(ex.getMessage());
                if(count < numRetries)
                {
                    Logger.info("Will retry in 5 seconds");
                    Thread.sleep(5000);
                }
                else
                {
                    throw new Exception("Could not download " + fromUrl);
                }
            }
        }
    }
    
    
    /**
     * Try downloading file once.
     * @param fromUrl source URL
     * @param toFile target file
     * @throws Exception an exception
     */
    private void downloadOnce(String fromUrl, File toFile) throws Exception
    {
        InputStream is = null;
        FileOutputStream os = null;
        
        Logger.info("Downloading " + fromUrl + " to " + toFile.getAbsolutePath());
        
        try
        {
            HttpURLConnection con = createConnection(new URL(fromUrl));
            os = new FileOutputStream(toFile);
            
            is = con.getInputStream();
            is.transferTo(os);
        }
        finally
        {
            CloseUtils.close(os);
            CloseUtils.close(is);
        }
    }


    /**
     * Create HTTP or HTTPS connection
     * @param url connect to this URL
     * @return HTTP connection
     * @throws Exception an exception
     */
    private HttpURLConnection createConnection(URL url) throws Exception
    {
        HttpURLConnection con = (HttpURLConnection)url.openConnection();
        if(con instanceof HttpsURLConnection)
        {
            HttpsURLConnection tlsCon = (HttpsURLConnection)con;

            if(sslTrustAll)
            {
                // Trust invalid / self-signed certificates
                SSLContext sc = SSLUtils.createTrustAllContext();
                tlsCon.setSSLSocketFactory(sc.getSocketFactory());

                // Do not verify host name (CN=host)
                tlsCon.setHostnameVerifier(new HostnameVerifier()
                {
                    @Override
                    public boolean verify(String hostname, SSLSession session)
                    {
                        return true;
                    }
                });
            }
        }
        
        con.setConnectTimeout(timeout);
        con.setReadTimeout(timeout);
        con.setAllowUserInteraction(false);
        
        return con;
    }

}
