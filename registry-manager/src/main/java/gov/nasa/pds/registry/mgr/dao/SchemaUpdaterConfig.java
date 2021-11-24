package gov.nasa.pds.registry.mgr.dao;

import java.io.File;

/**
 * Configuration parameters for SchemaUpdater class.
 *  
 * @author karpenko
 */
public class SchemaUpdaterConfig
{
    /**
     * Elasticsearch index name
     */
    public String indexName;
    
    /**
     * A URL pointing to an LDD configuration (LDD list) file.
     */
    public String lddCfgUrl;
    
    /**
     * Temporary directory to download LDDs and for other temporary files.
     */
    public File tempDir;
    

    /**
     * Constructor
     * @param indexName Elasticsearch index name
     * @param lddCfgUrl A URL pointing to an LDD configuration (LDD list) file.
     */
    public SchemaUpdaterConfig(String indexName, String lddCfgUrl)
    {
        this.indexName = indexName;
        this.lddCfgUrl = lddCfgUrl;
        this.tempDir = new File(System.getProperty("java.io.tmpdir"));
    }
}
