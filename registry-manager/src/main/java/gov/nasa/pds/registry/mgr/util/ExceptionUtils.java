package gov.nasa.pds.registry.mgr.util;


/**
 * Extract original exception message from nested stack trace.
 *  
 * @author karpenko
 */
public class ExceptionUtils
{
    /**
     * Extract original exception message from nested stack trace.
     * @param ex Parent exception
     * @return original exception message
     */
    public static String getMessage(Exception ex)
    {
        if(ex == null) return "";
        
        Throwable tw = ex;
        while(tw.getCause() != null)
        {
            tw = tw.getCause();
        }
        
        return tw.getMessage();
    }

}
