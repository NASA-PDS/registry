package gov.nasa.pds.registry.mgr.util;

/**
 * Very simple logger
 * @author karpenko
 */
public class Logger
{
    public static final int LEVEL_DEBUG = 10;
    public static final int LEVEL_INFO = 20;
    public static final int LEVEL_WARN = 30;
    public static final int LEVEL_ERROR = 40;
    
    private static int level = LEVEL_INFO;
    
    /**
     * Set logging level
     * @param level level
     */
    public static void setLevel(int level)
    {
        Logger.level = level;
    }
    
    
    /**
     * Print debug message
     * @param msg a message
     */
    public static void debug(String msg)
    {
        if(level > LEVEL_DEBUG) return;
        System.out.println("[DEBUG] " + msg);
    }

    
    /**
     * Print info message
     * @param msg a message
     */
    public static void info(String msg)
    {
        if(level > LEVEL_INFO) return;
        System.out.println("[INFO] " + msg);
    }

    
    /**
     * Print warning message
     * @param msg a message
     */
    public static void warn(String msg)
    {
        if(level > LEVEL_WARN) return;
        System.out.println("[WARN] " + msg);
    }


    /**
     * Print error message
     * @param msg a message
     */
    public static void error(String msg)
    {
        System.out.println("[ERROR] " + msg);
    }

}
