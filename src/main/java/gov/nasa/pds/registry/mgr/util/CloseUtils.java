package gov.nasa.pds.registry.mgr.util;

import java.io.Closeable;

/**
 * Close resources without throwing exceptions.
 *  
 * @author karpenko
 */
public class CloseUtils
{
    /**
     * Close resources without throwing exceptions.
     * @param cl a closeable object
     */
    public static void close(Closeable cl)
    {
        if(cl == null) return;
        
        try
        {
            cl.close();
        }
        catch(Exception ex)
        {
            // Ignore
        }
    }

}
