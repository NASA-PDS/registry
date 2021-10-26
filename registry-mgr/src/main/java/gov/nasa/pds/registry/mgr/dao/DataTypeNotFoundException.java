package gov.nasa.pds.registry.mgr.dao;

/**
 *  Throw this exception when the data type for a new registry field 
 *  is not found in the data dictionary and Elasticsearch schema 
 *  could not be updated.
 *  
 * @author karpenko
 */
@SuppressWarnings("serial")
public class DataTypeNotFoundException extends Exception
{
    /**
     * Constructor
     * @param fieldName Elasticsearch field name
     */
    public DataTypeNotFoundException(String fieldName)
    {
        super("Could not find datatype for field '" + fieldName + "'. " 
                + "See 'https://nasa-pds.github.io/pds-registry-app/operate/common-ops.html#Load' for more information.");
    }
}
