package gov.nasa.pds.registry.mgr.util.es;

import java.io.Closeable;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.io.StringWriter;

import com.google.gson.Gson;
import com.google.gson.stream.JsonWriter;

import gov.nasa.pds.registry.common.es.client.SearchResponseParser;

/**
 * <p>
 * Elasticsearch document writer.
 * Writes documents in "new-line-delimited JSON" format. (Content-Type: application/x-ndjson).
 * </p>
 * <p>
 * Generated file can be loaded into Elasticsearch by "_bulk" web service API: 
 * </p>
 * <pre>
 * curl -H "Content-Type: application/x-ndjson" \
 *      -XPOST "http://localhost:9200/accounts/_bulk?pretty" \
 *      --data-binary @es-docs.json
 * </pre>
 * 
 * @author karpenko
 */
public class EsDocWriter implements Closeable, SearchResponseParser.Callback
{
    private FileWriter writer;
    private Gson gson;
    
    /**
     * Constructor
     * @param file output file
     * @throws IOException an exception
     */
    public EsDocWriter(File file) throws IOException
    {
        writer = new FileWriter(file);
        gson = new Gson();
    }

    
    /**
     * Close file
     */
    @Override
    public void close() throws IOException
    {
        writer.close();
    }


    /**
     * Search response parser callback implementation.
     * This method is called for every record.
     */
    @Override
    public void onRecord(String id, Object rec) throws IOException
    {
        // 1st line: ID
        writePK(id);
        newLine();

        // 2nd line: data
        gson.toJson(rec, writer);
        newLine();
    }


    private void newLine() throws IOException
    {
        writer.write("\n");
    }

    
    /**
     * Write index primary key
     * @param id primary key
     * @throws IOException an exception
     */
    private void writePK(String id) throws IOException
    {
        StringWriter sw = new StringWriter();
        JsonWriter jw = new JsonWriter(sw);
        
        jw.beginObject();
        
        jw.name("index");
        jw.beginObject();
        jw.name("_id").value(id);
        jw.endObject();
        
        jw.endObject();
        
        jw.close();
        
        writer.write(sw.getBuffer().toString());
    }

}
