package gov.nasa.pds.registry.common.es.client;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;

import org.elasticsearch.client.Response;


/**
 * Debug utilities.
 * 
 * @author karpenko
 */
public class DebugUtils
{
    /**
     * Print Elasticsearch API response.
     * @param resp HTTP response
     * @throws IOException an exception
     */
    public static void dumpResponseBody(Response resp) throws IOException
    {
        InputStream is = resp.getEntity().getContent();
        dump(is);
        is.close();
    }
    

    /**
     * Print content of an input stream.
     * @param is input stream
     * @throws IOException an exception
     */
    public static void dump(InputStream is) throws IOException
    {
        BufferedReader rd = new BufferedReader(new InputStreamReader(is));
        
        String line;
        while((line = rd.readLine()) != null)
        {
            System.out.println(line);
        }
    }
}
