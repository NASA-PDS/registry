package gov.nasa.pds.registry.mgr.dao;

import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.List;

import org.apache.http.HttpEntity;

import com.google.gson.stream.JsonReader;
import com.google.gson.stream.JsonToken;


/**
 *  This class is used by SchemaDao to parse response from Elasticsearch 
 *  data dictionary query to get data types for a list of field ids.
 *   
 * @author karpenko
 */
public class GetDataTypesResponseParser
{
    /**
     * Inner class to store one response record.
     * @author karpenko
     */
    public static class Record
    {
        /**
         * Field ID
         */
        public String id;
        
        /**
         * True if field ID was found in the data dictionary
         */
        public boolean found;
        
        /**
         * Elasticsearch data type.
         */
        public String esDataType;
    }
    
    
    private JsonReader rd;


    /**
     * Constructor
     */
    public GetDataTypesResponseParser()
    {
    }
    
    
    /**
     * Parse HTTP body of a multi-get response (JSON)
     * @param entity HTTP response
     * @return a list of records
     * @throws IOException an exception
     */
    public List<Record> parse(HttpEntity entity) throws IOException
    {
        List<Record> records = new ArrayList<>();
        
        InputStream is = entity.getContent();
        rd = new JsonReader(new InputStreamReader(is));
    
        rd.beginObject();
        
        while(rd.hasNext() && rd.peek() != JsonToken.END_OBJECT)
        {
            String name = rd.nextName();
            if("docs".equals(name))
            {
                rd.beginArray();
                while(rd.hasNext() && rd.peek() != JsonToken.END_ARRAY)
                {
                    Record rec = parseDoc();
                    records.add(rec);
                }
                rd.endArray();
            }
            else
            {
                rd.skipValue();
            }
        }
        
        rd.endObject();
        rd.close();
        
        return records;
    }
    
    
    /**
     * Parse document sub-tree
     * @return a record
     * @throws IOException an exception
     */
    private Record parseDoc() throws IOException
    {
        Record rec = new Record();
        
        rd.beginObject();
        
        while(rd.hasNext() && rd.peek() != JsonToken.END_OBJECT)
        {
            String name = rd.nextName();
            if("_id".equals(name))
            {
                rec.id = rd.nextString();
            }
            else if("found".equals(name))
            {
                rec.found = rd.nextBoolean();
            }
            else if("_source".equals(name))
            {
                parseSource(rec);
            }
            else
            {
                rd.skipValue();
            }
        }
        
        rd.endObject();
        
        return rec;
    }
    
    
    /**
     * Parse Elasticsearch document "_source" field and extract "es_data_type" value.  
     * @param rec Update this object
     * @throws IOException an exception
     */
    protected void parseSource(Record rec) throws IOException
    {
        rd.beginObject();
        
        while(rd.hasNext() && rd.peek() != JsonToken.END_OBJECT)
        {
            String name = rd.nextName();
            if("es_data_type".equals(name))
            {
                rec.esDataType = rd.nextString();
            }
            else
            {
                rd.skipValue();
            }
        }
        
        rd.endObject();
    }

}
