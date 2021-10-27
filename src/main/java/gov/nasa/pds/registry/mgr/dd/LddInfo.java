package gov.nasa.pds.registry.mgr.dd;

import java.time.Instant;

/**
 * PDS LDD information
 * @author karpenko
 */
public class LddInfo
{
    /**
     * LDD Namespace, such as "pds" or "cart".
     */
    public String namespace;
    
    /**
     * Url pointing to LDD JSON file, such as
     * "https://pds.nasa.gov/pds4/pds/v1/PDS4_PDS_JSON_1F00.JSON" 
     */
    public String url;
    
    /**
     * LDD date stored as ISO Instant, e.g., "2020-12-23T15:16:28Z".
     */
    public Instant date;
    
    /**
     * Constructor
     * @param namespace LDD namespace
     * @param url URL pointing to LDD JSON file
     * @param date LDD date
     */
    public LddInfo(String namespace, String url, Instant date)
    {
        this.namespace = namespace;
        this.url = url;
        this.date = date;
    }
}
