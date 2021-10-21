package gov.nasa.pds.harvest.crawler;


/**
 * Product and collection reference cache. A singleton.
 * @author karpenko
 */
public class RefsCache
{
    private static RefsCache instance = new RefsCache();

    private LidVidCache prodRefsCache;
    private LidVidCache collectionRefsCache;
    
    
    /**
     * Private constructor. Use getInstance() instead.
     */
    private RefsCache()
    {
        prodRefsCache = new LidVidCache();
        collectionRefsCache = new LidVidCache();
    }

    
    /**
     * Get singleton instance.
     * @return Reference cache
     */
    public static RefsCache getInstance()
    {
        return instance;
    }

    
    /**
     * Get product reference cache.
     * @return LidVid cache
     */
    public LidVidCache getProdRefsCache()
    {
        return prodRefsCache;
    }


    /**
     * Get collection reference cache.
     * @return LidVid cache
     */
    public LidVidCache getCollectionRefsCache()
    {
        return collectionRefsCache;
    }

}
