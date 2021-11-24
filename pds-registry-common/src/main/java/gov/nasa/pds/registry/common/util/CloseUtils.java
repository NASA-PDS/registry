package gov.nasa.pds.registry.common.util;

import java.io.Closeable;

/**
 * Utility class to close resources without throwing exceptions.
 * 
 * @author karpenko
 */
public class CloseUtils
{
    public static void close(Closeable cl)
    {
        if(cl == null) return;
        
        try
        {
            cl.close();
        }
        catch(Exception ex)
        {
            // Ignore exception
        }
    }

}
