package gov.nasa.pds.registry.mgr;

/**
 * Some constants used by different classes.
 *  
 * @author karpenko
 */
public interface Constants
{
    // Indices
    public static final String DEFAULT_REGISTRY_INDEX = "registry";

    // Fields
    public static final String NS_SEPARATOR = ":";
    public static final String ATTR_SEPARATOR = "/";
    public static final String BLOB_FIELD = "ops:Label_File_Info/ops:blob";
    
    // LDDs
    public static final String DEFAULT_LDD_LIST_URL 
        = "https://raw.githubusercontent.com/NASA-PDS/pds4-information-model/main/docs/ldds/pds4-ldd-config.csv";
}
