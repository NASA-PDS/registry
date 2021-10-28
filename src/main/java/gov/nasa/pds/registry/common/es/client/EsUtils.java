package gov.nasa.pds.registry.common.es.client;


import java.util.List;
import java.util.Map;

import org.apache.http.HttpHost;
import org.elasticsearch.client.Response;
import org.elasticsearch.client.ResponseException;

import com.google.gson.Gson;


/**
 * Elasticsearch utility methods.
 * 
 * @author karpenko
 */
public class EsUtils
{
    /**
     * Parse Elasticsearch URL
     * @param url Elasticsearch URL, e.g., "http://localhost:9200"
     * @return HTTP host information
     * @throws Exception an exception
     */
    public static HttpHost parseEsUrl(String url) throws Exception
    {
        if(url == null) throw new Exception("URL is null");
        
        String tmpUrl = url.trim();

        String proto = "http";
        String host = null;
        int port = 9200;
        
        // Protocol
        int idx = tmpUrl.indexOf("://");
        if(idx > 0)
        {
            proto = tmpUrl.substring(0, idx).toLowerCase();
            if(!proto.equals("http") && !proto.equals("https")) 
            {
                throw new Exception("Invalid protocol '" + proto + "'. Expected 'http' or 'https'.");
            }
            
            tmpUrl = tmpUrl.substring(idx + 3);
        }
        
        // Host & port
        idx = tmpUrl.indexOf(":");
        if(idx > 0)
        {
            host = tmpUrl.substring(0, idx);
            
            // Port
            String strPort = tmpUrl.substring(idx + 1);
            idx = strPort.indexOf("/");
            if(idx > 0)
            {
                strPort = strPort.substring(0, idx);
            }
            
            try
            {
                port = Integer.parseInt(strPort);
            }
            catch(Exception ex)
            {
                throw new Exception("Invalid port " + strPort);
            }
        }
        // Host only
        else
        {
            host = tmpUrl;
            idx = host.indexOf("/");
            if(idx > 0)
            {
                host = host.substring(0, idx);
            }
        }
        
        HttpHost httpHost = new HttpHost(host, port, proto);
        return httpHost;
    }
    
    
    /**
     * Extract error message from Elasticsearch response exception.
     * @param ex an exception
     * @return error message
     */
    public static String extractErrorMessage(ResponseException ex)
    {
        String msg = ex.getMessage();
        if(msg == null) return "Unknown error";
        
        String lines[] = msg.split("\n");
        if(lines.length < 2) return msg;
        
        String reason = extractReasonFromJson(lines[1]);
        if(reason == null) return msg;
        
        return reason;
    }
    
    
    /**
     * Extract error message from Elasticsearch response JSON.
     * @param json response JSON
     * @return error message
     */
    @SuppressWarnings("rawtypes")
    public static String extractReasonFromJson(String json)
    {
        try
        {
            Gson gson = new Gson();
            Object obj = gson.fromJson(json, Object.class);
            
            obj = ((Map)obj).get("error");
            
            Object rc = ((Map)obj).get("root_cause");
            if(rc != null)
            {
                List list = (List)rc;
                obj = ((Map)list.get(0)).get("reason");
            }
            else
            {
                obj = ((Map)obj).get("reason");
            }
            
            return obj.toString();
        }
        catch(Exception ex)
        {
            return null;
        }
    }

    
    /**
     * Print Elasticsearch response warnings.
     * @param resp HTTP response
     */
    public static void printWarnings(Response resp)
    {
        List<String> warnings = resp.getWarnings();
        if(warnings != null)
        {
            for(String warn: warnings)
            {
                System.out.println("[WARN] " + warn);
            }
        }
    }
}
