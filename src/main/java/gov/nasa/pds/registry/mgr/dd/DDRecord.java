package gov.nasa.pds.registry.mgr.dd;

import gov.nasa.pds.registry.mgr.Constants;

/**
 * Data dictionary record to be stored in Elasticsearch
 * 
 * @author karpenko
 */
public class DDRecord
{
    public String esFieldName;
    public String esDataType;
    
    public String classNs;
    public String className;
    
    public String attrNs;
    public String attrName;
    
    public String description;
    public String dataType;

    public String imVersion;
    public String lddVersion;
    public String date;
    
    
    /**
     * Constructor
     */
    public DDRecord()
    {        
    }
    
    
    /**
     * Get Elasticsearch field name from individual components
     * (class_namespace:ClassName/attribute_namespace:AttributeName)
     * @return Elasticsearch field name
     */
    public String esFieldNameFromComponents()
    {
        return classNs + Constants.NS_SEPARATOR + className + Constants.ATTR_SEPARATOR 
                + attrNs + Constants.NS_SEPARATOR + attrName;
    }
}
