package gov.nasa.pds.registry.mgr.dao;

import java.io.IOException;
import java.io.StringWriter;
import java.io.Writer;
import java.util.Collection;
import java.util.List;

import com.google.gson.stream.JsonWriter;

import gov.nasa.pds.registry.mgr.util.Tuple;

/**
 * Methods to build JSON requests for Elasticsearch APIs.
 * @author karpenko
 */
public class SchemaRequestBuilder
{
    private boolean pretty;

    /**
     * Constructor
     * @param pretty Format JSON for humans to read.
     */
    public SchemaRequestBuilder(boolean pretty)
    {
        this.pretty = pretty;
    }

    /**
     * Constructor
     */
    public SchemaRequestBuilder()
    {
        this(false);
    }

    
    protected JsonWriter createJsonWriter(Writer writer)
    {
        JsonWriter jw = new JsonWriter(writer);
        if (pretty)
        {
            jw.setIndent("  ");
        }

        return jw;
    }

    
    /**
     * Create multi get (_mget) request.
     * @param ids list of IDs
     * @return JSON
     * @throws IOException an exception
     */
    public String createMgetRequest(Collection<String> ids) throws IOException
    {
        StringWriter wr = new StringWriter();
        JsonWriter jw = createJsonWriter(wr);

        jw.beginObject();
        jw.name("ids");
        
        jw.beginArray();
        for(String id: ids)
        {
            jw.value(id);
        }
        jw.endArray();
        
        jw.endObject();
        jw.close();        

        return wr.toString();        
    }
    
    
    /**
     * Create update Elasticsearch schema request
     * @param fields A list of fields to add. Each field tuple has a name and a data type.
     * @return Elasticsearch query in JSON format
     * @throws IOException an exception
     */
    public String createUpdateSchemaRequest(List<Tuple> fields) throws IOException
    {
        StringWriter wr = new StringWriter();
        JsonWriter jw = createJsonWriter(wr);

        jw.beginObject();
        
        jw.name("properties");
        jw.beginObject();
        for(Tuple field: fields)
        {
            jw.name(field.item1);
            jw.beginObject();
            jw.name("type").value(field.item2);
            jw.endObject();            
        }
        jw.endObject();
        
        jw.endObject();
        jw.close();        

        return wr.toString();        
    }


    /**
     * Create get data dictionary (LDD) info request.
     * @param namespace LDD namespace ID, such as 'pds', 'cart', etc.
     * @return Elasticsearch query in JSON format
     * @throws IOException an exception
     */
    public String createGetLddInfoRequest(String namespace) throws IOException
    {
        StringWriter wr = new StringWriter();
        JsonWriter jw = createJsonWriter(wr);

        jw.beginObject();

        // Start query
        jw.name("query");
        jw.beginObject();
        jw.name("ids");
        jw.beginObject();
        
        jw.name("values");
        jw.beginArray();
        jw.value("registry:LDD_Info/registry:" + namespace);
        jw.endArray();
        
        jw.endObject();
        jw.endObject();
        // End query
        
        // Start source
        jw.name("_source");
        jw.beginArray();
        jw.value("date").value("version");
        jw.endArray();        
        // End source
        
        jw.endObject();
        jw.close();        

        return wr.toString();        
    }
}
