package gov.nasa.pds.registry.common.es.client;

import java.io.InputStream;
import java.io.InputStreamReader;

import org.elasticsearch.client.Response;

import com.google.gson.Gson;
import com.google.gson.stream.JsonReader;
import com.google.gson.stream.JsonToken;


/**
 * Helper class to parse search API's JSON responses. 
 * 
 * @author karpenko
 */
public class SearchResponseParser
{
    /**
     * Inner callback interface
     * @author karpenko
     */
    public static interface Callback
    {
        /**
         * This method is called for each record in response JSON.
         * @param id record ID / primary key
         * @param rec Parsed content of "_source" field. Usually it is a field name-value map.
         * @throws Exception an exception
         */
        public void onRecord(String id, Object rec) throws Exception;
    }
    
    
    private Callback cb;
    private Gson gson = new Gson();
    private String lastId;
    private int numDocs;

    
    /**
     * Constructor
     */
    public SearchResponseParser()
    {
    }

    
    /**
     * This method is used by searchAfter API to paginate results. 
     * @return ID of the last parsed record
     */
    public String getLastId()
    {
        return lastId;
    }

    
    /**
     * Get number of parsed documents.
     * @return number of parsed documents
     */
    public int getNumDocs()
    {
        return numDocs;
    }


    /**
     * Parse response. Callback.onRecord() will be called for each record.
     * @param resp Elasticsearch rest client's response object.
     * @param cb Callback interface.
     * @throws Exception an exception
     */
    public void parseResponse(Response resp, Callback cb) throws Exception
    {
        if(cb == null) throw new IllegalArgumentException("Callback is null");
        this.cb = cb;
        
        lastId = null;
        numDocs = 0;
        
        InputStream is = resp.getEntity().getContent();
        JsonReader rd = new JsonReader(new InputStreamReader(is));
        
        rd.beginObject();
        
        while(rd.hasNext() && rd.peek() != JsonToken.END_OBJECT)
        {
            String name = rd.nextName();
            if("hits".equals(name))
            {
                parseHits(rd);
            }
            else
            {
                rd.skipValue();
            }
        }
        
        rd.endObject();
        
        rd.close();
    }
    
    
    /**
     * Parse "hits" array in JSON response.
     * @param rd JSON reader
     * @throws Exception an exception
     */
    private void parseHits(JsonReader rd) throws Exception
    {
        rd.beginObject();
        
        while(rd.hasNext() && rd.peek() != JsonToken.END_OBJECT)
        {
            String name = rd.nextName();
            if("hits".equals(name))
            {
                rd.beginArray();
                while(rd.hasNext() && rd.peek() != JsonToken.END_ARRAY)
                {
                    parseHit(rd);
                }
                rd.endArray();
            }
            else
            {
                rd.skipValue();
            }
        }
        
        rd.endObject();
    }


    /**
     * Parse a hit from "hits" array in JSON response.
     * @param rd JSON reader
     * @throws Exception an exception
     */
    private void parseHit(JsonReader rd) throws Exception
    {
        Object src = null;
        
        rd.beginObject();

        while(rd.hasNext() && rd.peek() != JsonToken.END_OBJECT)
        {
            String name = rd.nextName();
            // Parse primary key
            if("_id".equals(name))
            {
                lastId = rd.nextString();
            }
            // Parse "_source" field. Usually it will be a Map.
            else if("_source".equals(name))
            {
                src = gson.fromJson(rd, Object.class);
            }
            else
            {
                rd.skipValue();
            }
        }
        
        rd.endObject();

        numDocs++;
        cb.onRecord(lastId, src);
    }    

}
