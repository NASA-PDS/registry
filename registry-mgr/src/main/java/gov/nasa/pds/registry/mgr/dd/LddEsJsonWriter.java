package gov.nasa.pds.registry.mgr.dd;

import java.io.File;
import java.util.Map;

import gov.nasa.pds.registry.mgr.dd.parser.DDAttribute;
import gov.nasa.pds.registry.mgr.util.Logger;


/**
 * Writes Elasticsearch JSON data file to be loaded into data dictionary index.
 * 
 * @author karpenko
 */
public class LddEsJsonWriter
{
    private DDNJsonWriter writer;
    private DDRecord ddRec = new DDRecord();
    
    private Pds2EsDataTypeMap dtMap;
    private Map<String, DDAttribute> ddAttrCache;
    private String nsFilter;
    

    /**
     * Constructor
     * @param outFile Elasticsearch JSON data file
     * @param dtMap PDS to Elasticsearch data type map
     * @param ddAttrCache LDD attribute cache
     * @throws Exception an exception
     */
    public LddEsJsonWriter(File outFile, Pds2EsDataTypeMap dtMap, Map<String, DDAttribute> ddAttrCache) throws Exception
    {
        writer = new DDNJsonWriter(outFile);
        this.dtMap = dtMap;
        this.ddAttrCache = ddAttrCache;
    }

    
    /**
     * Set namespace filter. Only process classes having this namespace.
     * @param filter namespace, such as 'pds'
     */
    public void setNamespaceFilter(String filter)
    {
        this.nsFilter = filter;
    }
    
    
    /**
     * Close output file
     * @throws Exception an exception
     */
    public void close() throws Exception
    {
        writer.close();
    }

    
    /**
     * Write field definition (Elasticsearch field name, data type and other information)
     * @param classNs LDD class namespace
     * @param className LDD class name
     * @param attrId LDD attribute ID
     * @throws Exception an exception
     */
    public void writeFieldDefinition(String classNs, String className, String attrId) throws Exception
    {
        // Apply namespace filter
        if(nsFilter != null && !nsFilter.equals(classNs)) return;        

        DDAttribute attr = ddAttrCache.get(attrId);
        if(attr == null)
        {
            Logger.warn("Missing attribute " + attrId);
        }
        else
        {
            writeRecord(classNs, className, attr);
        }
    }

    
    /**
     * Write PDS LDD version and date
     * @param namespace LDD namespace
     * @param version LDD version
     * @param date LDD date
     * @throws Exception an exception
     */
    public void writeDataDictionaryVersion(String namespace, String imVersion, 
            String lddVersion, String date) throws Exception
    {
        if(namespace == null || namespace.isBlank()) throw new IllegalArgumentException("Missing data dictionary namespace");
        if(date == null || date.isBlank()) throw new IllegalArgumentException("Missing data dictionary date");
        
        DDRecord rec = new DDRecord();
        rec.classNs = "registry";
        rec.className = "LDD_Info";
        rec.attrNs = "registry";
        rec.attrName = namespace;
        
        rec.imVersion = imVersion;
        rec.lddVersion = lddVersion;
        rec.date = LddUtils.lddDateToIsoInstant(date);
        
        writer.write(rec.esFieldNameFromComponents(), rec);
    }
    
    
    private void writeRecord(String classNs, String className, DDAttribute dda) throws Exception
    {
        // Assign values
        ddRec.classNs = classNs;
        ddRec.className = className;
        ddRec.attrNs = dda.attrNs;
        ddRec.attrName = dda.attrName;
        
        ddRec.dataType = dda.dataType;
        ddRec.esDataType = dtMap.getEsDataType(dda.dataType);
        
        ddRec.description = dda.description;

        // Write
        writer.write(ddRec.esFieldNameFromComponents(), ddRec);
    
        // Fix wrong attribute namespace
        if(!classNs.equals(dda.attrNs))
        {
            ddRec.attrNs = classNs;
            writer.write(ddRec.esFieldNameFromComponents(), ddRec);
        }
    }
        
}
