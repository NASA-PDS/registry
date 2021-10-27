package gov.nasa.pds.registry.mgr.dd.parser;

import java.io.File;
import java.io.FileReader;

import com.google.gson.stream.JsonReader;
import com.google.gson.stream.JsonToken;

import gov.nasa.pds.registry.mgr.util.CloseUtils;

/**
 * Base parser of PDS LDD JSON files (Data dictionary files).
 * This implementation is using Google "GSON" streaming parser to reduce memory footprint.
 * (We only need a subset of values from a JSON file).
 *  
 * @author karpenko
 */
public class BaseLddParser
{
    protected File ddFile;
    protected JsonReader jsonReader;
    
    protected String imVersion;
    protected String lddVersion;
    protected String ddDate;
    
    
    /**
     * Constructor
     * @param file PDS LDD JSON file to parse
     * @throws Exception an exception
     */
    public BaseLddParser(File file) throws Exception
    {
        this.ddFile = file;
        jsonReader = new JsonReader(new FileReader(file));
    }

    /**
     * Returns LDD version
     * @return LDD version
     */
    public String getLddVersion()
    {
        return lddVersion;
    }

    
    /**
     * Returns Information Model version
     * @return Information Model version
     */
    public String getImVersion()
    {
        return imVersion;
    }

    
    /**
     * Returns LDD (creation) date
     * @return LDD date
     */
    public String getLddDate()
    {
        return ddDate;
    }
    
    /**
     * Parse PDS LDD JSON file
     * @throws Exception an exception
     */
    public void parse() throws Exception
    {
        try
        {
            parseRoot();
        }
        finally
        {
            CloseUtils.close(jsonReader);
        }
    }
    
    
    /**
     * Parse root element
     * @throws Exception an exception
     */
    private void parseRoot() throws Exception
    {
        jsonReader.beginArray();
        
        while(jsonReader.hasNext() && jsonReader.peek() != JsonToken.END_ARRAY)
        {
            jsonReader.beginObject();

            while(jsonReader.hasNext() && jsonReader.peek() != JsonToken.END_OBJECT)
            {
                String name = jsonReader.nextName();
                if("dataDictionary".equals(name))
                {
                    parseDataDic();
                }
                else
                {
                    jsonReader.skipValue();
                }
            }
            
            jsonReader.endObject();
        }
        
        jsonReader.endArray();
    }
    
    
    /**
     * Parse "dataDictionary" -&gt; "classDictionary" subtree
     * @throws Exception an exception
     */
    protected void parseClassDictionary() throws Exception
    {
        jsonReader.skipValue();
    }
    

    /**
     * Parse "dataDictionary" -&gt; "attributeDictionary" subtree
     * @throws Exception an exception
     */
    protected void parseAttributeDictionary() throws Exception
    {
        jsonReader.skipValue();
    }

    
    /**
     * Parse "dataDictionary" subtree
     * @throws Exception an exception
     */
    private void parseDataDic() throws Exception
    {
        jsonReader.beginObject();

        while(jsonReader.hasNext() && jsonReader.peek() != JsonToken.END_OBJECT)
        {
            String name = jsonReader.nextName();
            
            if("Version".equals(name))
            {
                imVersion = jsonReader.nextString();
            }
            else if("IM Version".equals(name))
            {
                imVersion = jsonReader.nextString();
            }
            else if("LDD Version".equals(name))
            {
                lddVersion = jsonReader.nextString();
            }
            else if("Date".equals(name))
            {
                ddDate = jsonReader.nextString();
            }
            else if("classDictionary".equals(name))
            {
                parseClassDictionary();
            }
            else if("attributeDictionary".equals(name))
            {
                parseAttributeDictionary();
            }
            else
            {
                jsonReader.skipValue();
            }
        }
        
        jsonReader.endObject();
    }

}
