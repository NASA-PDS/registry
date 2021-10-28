package gov.nasa.pds.registry.common.util;

import java.io.FileReader;
import java.util.Properties;


/**
 * Utility class to read java properties files.
 * 
 * @author karpenko
 */
public class JavaProps
{
    private Properties props;
    
    
    /**
     * Constructor
     * @param filePath Java properties file
     * @throws Exception an exception
     */
    public JavaProps(String filePath) throws Exception
    {
        if(filePath == null) throw new IllegalArgumentException("File path is null");
        
        props = new Properties();
        FileReader rd = new FileReader(filePath);
        
        try
        {
            props.load(rd);
        }
        finally
        {
            CloseUtils.close(rd);
        }
    }
    
    
    /**
     * Get boolean property.
     * @param key property key / name
     * @return boolean value
     * @throws Exception an exception
     */
    public Boolean getBoolean(String key) throws Exception
    {
        if(props == null) return null;
        
        String str = props.getProperty(key);
        if(str == null) return null;

        if(!str.equals("true") && str.equals("false")) 
        {
            throw new Exception("Property " + key + " has invalid value " + str);
        }
        
        return str.equals("true");
    }
    
    
    /**
     * Get string property.
     * @param key property key / name
     * @return String value
     */
    public String getProperty(String key)
    {
        return props.getProperty(key);
    }
    
}
